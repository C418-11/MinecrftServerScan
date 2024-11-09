# -*- coding: utf-8 -*-
# cython: language_level = 3

__author__ = "C418____11 <553515788@qq.com>"
__version__ = "0.0.1"

import functools
import inspect
import os.path
from abc import ABC
from abc import abstractmethod
from collections import OrderedDict
from collections.abc import Mapping
from collections.abc import MutableMapping
from copy import deepcopy
from enum import Enum
from types import UnionType
from typing import Any
from typing import Callable
from typing import Iterable
from typing import Optional
from typing import Self
from typing import Sequence
from typing import TypeVar
from typing import override


class ConfigOperate(Enum):
    """
    对配置的操作类型
    """
    Delete = "Delete"
    Read = "Read"
    Write = "Write"
    Unknown = None


class RequiredKeyNotFoundError(KeyError):
    """
    需求的键未找到错误
    """

    def __init__(
            self,
            key: str,
            sep_char: str,
            current_key: str,
            index: int,
            operate: ConfigOperate = ConfigOperate.Unknown,
    ):
        """
        :param key: 完整键路径
        :type key: str
        :param sep_char: 键路径的分隔符
        :type sep_char: str
        :param current_key: 当前正在访问的键
        :type current_key: str
        :param index: 当前访问的键在完整键路径中的索引
        :type index: int
        :param operate: 何种操作过程中发生的该错误
        :type operate: ConfigOperate
        """
        super().__init__(current_key)

        self.key = key
        self.sep_char = sep_char
        self.current_key = current_key
        self.index = index
        self.operate = ConfigOperate(operate)

    def __str__(self):
        string = f"{self.key} -> {self.current_key} ({self.index + 1} / {len(self.key.split(self.sep_char))})"
        if self.operate.value is not ConfigOperate.Unknown:
            string += f" Operate: {self.operate.value}"
        return string


class ConfigDataTypeError(TypeError):
    """
    配置数据类型错误
    """

    def __init__(
            self,
            key: str,
            sep_char: str,
            current_key: str,
            index: int,
            required_type: type[object],
            now_type: type[object],
    ):
        """
        :param key: 完整键路径
        :type key: str
        :param sep_char: 键路径的分隔符
        :type sep_char: str
        :param current_key: 当前正在访问的键
        :type current_key: str
        :param index: 当前访问的键在完整键路径中的索引
        :type index: int
        :param required_type: 该键需求的数据类型
        :type required_type: type[object]
        :param now_type: 当前键的数据类型
        :type now_type: type[object]
        """
        super().__init__(current_key)

        self.key = key
        self.sep_char = sep_char
        self.current_key = current_key
        self.index = index
        self.requited_type = required_type
        self.now_type = now_type

    def __str__(self):
        return (
            f"{self.key} -> {self.current_key} ({self.index + 1} / {len(self.key.split(self.sep_char))})"
            f" Must be '{self.requited_type}'"
            f", Not '{self.now_type}'"
        )


class UnsupportedConfigFormatError(Exception):
    """
    不支持的配置文件格式错误
    """

    def __init__(self, _format: str):
        """
        :param _format: 不支持的配置的文件格式
        :type _format: str
        """
        super().__init__(f"Unsupported config format: {_format}")
        self.format = _format


class FailedProcessConfigFileError(Exception):
    """
    SL处理器无法正确处理当前配置文件
    """

    def __init__(self, reason: BaseException | Iterable[BaseException] | Mapping[str, BaseException]):
        """
        :param reason: 处理配置文件失败的原因
        :type reason: BaseException | Iterable[BaseException] | Mapping[str, BaseException]
        """

        if isinstance(reason, Mapping):
            reason = OrderedDict(reason)
            super().__init__('\n'.join(map(lambda _: f"{_[0]}: {_[1]}", reason.items())))
        elif isinstance(reason, Iterable):
            reason = tuple(reason)
            super().__init__('\n'.join(map(str, reason)))
        else:
            reason = (reason,)
            super().__init__(str(reason))

        self.reasons: tuple[BaseException] | OrderedDict[str, BaseException] = reason


def _norm_join(*paths: str) -> str:
    return os.path.normpath(os.path.join(*paths))


def _is_method(func):
    arguments = inspect.getargs(func.__code__).args
    if len(arguments) < 1:
        return False
    return arguments[0] in {"self", "cls"}


D = TypeVar('D', Mapping, MutableMapping)


class ConfigData:
    """
    配置数据
    """

    def __init__(self, data: D = None, sep_char: str = '.'):
        """
        data为None时，默认为空字典

        如果data不继承自MutableMapping，则该配置数据被设为只读

        :param data: 配置的原始数据
        :type data: Mapping | MutableMapping
        """
        if data is None:
            data = {}
        self._data = deepcopy(data)
        self._data_read_only: bool = not isinstance(data, MutableMapping)
        self._read_only: bool = self._data_read_only

        self._sep_char: str = sep_char

    @property
    def data(self) -> D:
        """
        配置的原始数据*快照*
        """
        return deepcopy(self._data)

    @property
    def read_only(self) -> bool:
        return self._data_read_only or self._read_only

    @property
    def sep_char(self) -> str:
        return self._sep_char

    @read_only.setter
    def read_only(self, value: Any):
        if self._data_read_only:
            raise TypeError("ConfigData is read-only")
        self._read_only = bool(value)

    def _process_path(self, path: str, process_check: Callable, process_return: Callable) -> Any:
        """
        处理键路径的通用函数阿

        :param path: 键路径
        :type path: str
        :param process_check: 检查并处理每个路径段，返回值非None时结束操作并返回值
        :type process_check: Callable[(now_data: Any, now_path: str, last_path: str, path_index: int), Any]
        :param process_return: 处理最终结果，该函数返回值会被直接返回
        :type process_return: Callable[(now_data: Any), Any]

        :return: 处理结果
        :rtype: Any
        """
        last_path = path
        now_data = self._data

        path_index = -1

        while last_path:
            path_index += 1
            try:
                now_path, last_path = last_path.split(self._sep_char, maxsplit=1)
            except ValueError:
                now_path, last_path = last_path, None

            check_result = process_check(now_data, now_path, last_path, path_index)
            if check_result is not None:
                return check_result

            now_data = now_data[now_path]

        return process_return(now_data)

    def getPathValue(self, path: str, *, get_raw: bool = False) -> Any:
        """
        获取路径的值的*快照*

        :param path: 路径
        :type path: str
        :param get_raw: 是否获取原始值，为False时，会将Mapping转换为当前类
        :type get_raw: bool

        :return: 路径的值
        :rtype: Any

        :raise ConfigDataTypeError: 配置数据类型错误
        :raise RequiredKeyNotFoundError: 需求的键不存在
        """

        def checker(now_data, now_path, _last_path, path_index):
            if not isinstance(now_data, Mapping):
                raise ConfigDataTypeError(path, self._sep_char, now_path, path_index, Mapping, type(now_data))
            if now_path not in now_data:
                raise RequiredKeyNotFoundError(path, self._sep_char, now_path, path_index, ConfigOperate.Read)

        def process_return(now_data):
            if get_raw:
                return deepcopy(now_data)
            if isinstance(now_data, Mapping):
                return ConfigData(deepcopy(now_data))

            return deepcopy(now_data)

        return self._process_path(path, checker, process_return)

    def setPathValue(self, path: str, value: Any, *, allow_create: bool = True) -> Self:
        """
        设置路径的值

        .. warning::
           value参数未默认做深拷贝，可能导致非预期的行为

        :param path: 路径
        :type path: str
        :param value: 值
        :type value: Any
        :param allow_create: 是否允许创建不存在的路径，默认为True
        :type allow_create: bool

        :return: 返回当前实例便于链式调用
        :rtype: Self

        :raise ConfigDataTypeError: 配置数据类型错误
        :raise RequiredKeyNotFoundError: 需求的键不存在
        """
        if self.read_only:
            raise TypeError("Config data is read-only")

        def checker(now_data, now_path, last_path, path_index):
            if not isinstance(now_data, MutableMapping):
                raise ConfigDataTypeError(path, self._sep_char, now_path, path_index, MutableMapping, type(now_data))
            if now_path not in now_data:
                if not allow_create:
                    raise RequiredKeyNotFoundError(path, self._sep_char, now_path, path_index, ConfigOperate.Write)
                now_data[now_path] = {}

            if last_path is None:
                now_data[now_path] = value

        self._process_path(path, checker, lambda *_: None)
        return self

    def deletePath(self, path: str) -> Self:
        """
        删除路径

        :param path: 路径
        :type path: str

        :return: 返回当前实例便于链式调用
        :rtype: Self

        :raise ConfigDataTypeError: 配置数据类型错误
        :raise RequiredKeyNotFoundError: 需求的键不存在
        """
        if self.read_only:
            raise TypeError("Config data is read-only")

        def checker(now_data, now_path, last_path, path_index):
            if not isinstance(now_data, MutableMapping):
                raise ConfigDataTypeError(path, self._sep_char, now_path, path_index, MutableMapping, type(now_data))
            if now_path not in now_data:
                raise RequiredKeyNotFoundError(path, self._sep_char, now_path, path_index, ConfigOperate.Delete)

            if last_path is None:
                del now_data[now_path]
                return True

        self._process_path(path, checker, lambda *_: None)
        return self

    def hasPath(self, path: str) -> bool:
        """
        判断路径是否存在

        :param path: 路径
        :type path: str

        :return: 路径是否存在
        :rtype: bool

        :raise ConfigDataTypeError: 配置数据类型错误
        """

        def checker(now_data, now_path, _last_path, path_index):
            if not isinstance(now_data, Mapping):
                raise ConfigDataTypeError(path, self._sep_char, now_path, path_index, Mapping, type(now_data))
            if now_path not in now_data:
                return False

        return self._process_path(path, checker, lambda *_: True)

    def get(self, path: str, default=None, *, get_raw: bool = False) -> Any:
        """
        获取路径的值

        :param path: 路径
        :type path: str

        :param default: 默认值
        :type default: Any
        :param get_raw: 是否获取原始值
        :type get_raw: bool

        :return: 值
        :rtype: Any

        :raise ConfigDataTypeError: 配置数据类型错误
        """
        try:
            return self.getPathValue(path, get_raw=get_raw)
        except RequiredKeyNotFoundError:
            return default

    def keys(self):
        return self._data.keys()

    def values(self):
        copied_values = [deepcopy(x) for x in self._data.values()]
        return [(type(self)(x) if isinstance(x, Mapping) else x) for x in copied_values]

    def items(self):
        copied_items = [(deepcopy(k), deepcopy(v)) for k, v in self._data.items()]
        return [(k, (type(self)(v) if isinstance(v, Mapping) else v)) for k, v in copied_items]

    def __getitem__(self, key):
        return self.getPathValue(key)

    def __setitem__(self, key, value) -> None:
        self.setPathValue(key, value)

    def __delitem__(self, key) -> None:
        self.deletePath(key)

    def __contains__(self, key) -> bool:
        return self.hasPath(key)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._data == other._data

    def __getattr__(self, item) -> Self | Any:
        item_obj = self._data[item]
        return type(self)(item_obj) if isinstance(item_obj, Mapping) else item_obj

    def __iter__(self):
        return iter(self._data)

    def __str__(self) -> str:
        return str(self._data)

    def __repr__(self) -> str:
        data_repr = f"{self._data!r}"
        if type(self) is dict:
            data_repr = data_repr[1:-1]

        return f"{self.__class__.__name__}({data_repr})"

    def __deepcopy__(self, memo) -> Self:
        return type(self)(deepcopy(self._data, memo))


class RequiredKey:
    """
    对需求的键进行存在检查、类型检查、填充默认值
    """
    TypingType = {UnionType}

    def __init__(self, paths: Iterable[str] | Mapping[str, Any]):
        """
        当paths为Mapping时{key: value}

        value会被作为key不存在时的*默认值*填充，在key存在时会进行isinstance(data, type(value))检查

        如果type(value) is type也就是*默认值*是类型时，会将其直接用作类型检查issubclass(data, value)且不会尝试填充默认值

        :param paths: 需求的路径
        :type paths: Iterable[str] | Mapping[str, Any]
        """

        self._check_type: bool = isinstance(paths, Mapping)
        self._paths: Iterable[str] | Mapping[str, type] = paths

    def filter(self, data: ConfigData, *, allow_create: bool = False, ignore_missing: bool = False) -> Any:
        """
        检查过滤需求的键

        .. note::
           返回的配置数据是*快照*

        :param data: 要过滤的原始数据
        :type data: ConfigData
        :param allow_create: 是否允许值不存在时修改data参数对象填充默认值(即使为False仍然会在结果中填充默认值,但不会修改data参数对象)
        :type allow_create: bool
        :param ignore_missing: 忽略丢失的键
        :type ignore_missing: bool

        :return: 处理后的配置数据*快照*
        :rtype: Any
        """
        result = type(data)()

        if not self._check_type:
            for path in self._paths:
                value = data.getPathValue(path)
                result[path] = value
            return result

        for path, default in self._paths.items():

            _type = default
            if (type(default) not in self.TypingType) and (type(default) is not type):
                _type = type(default)
                value = deepcopy(default)
                try:
                    value = data.getPathValue(path)
                except RequiredKeyNotFoundError:
                    if allow_create:
                        data.setPathValue(path, value, allow_create=True)
            else:
                try:
                    value = data.getPathValue(path)
                except RequiredKeyNotFoundError:
                    if not ignore_missing:
                        raise
                    continue

            if (type(default) not in self.TypingType) and issubclass(_type, Mapping) and isinstance(value, type(data)):
                value = value.data

            if not isinstance(value, _type):
                path_chunks = path.split(data.sep_char)
                raise ConfigDataTypeError(
                    path, data.sep_char, path_chunks[-1], len(path_chunks) - 1, _type, type(value)
                )

            result[path] = value

        return result


class ABCConfigPool(ABC):
    def __init__(self, root_path: str = "./.config"):
        self.root_path = root_path
        self.SLProcessor: dict[str, ABCConfigSL] = {}  # SaveLoadProcessor {RegName: Processor}
        self.FileExtProcessor: dict[str, set[str]] = {}  # {FileExt: {RegName}}


class ABCConfig(ABC):
    """
    配置文件类
    """

    def __init__(
            self,
            config_data: ConfigData,
            *,
            namespace: Optional[str] = None,
            file_name: Optional[str] = None,
            config_format: Optional[str] = None
    ) -> None:
        """
        :param config_data: 配置数据
        :type config_data: ConfigData
        :param namespace: 文件命名空间
        :type namespace: Optional[str]
        :param file_name: 文件名
        :type file_name: Optional[str]
        :param config_format: 配置文件的格式
        :type config_format: Optional[str]
        """

        self._data: ConfigData = config_data

        self._namespace: str | None = namespace
        self._file_name: str | None = file_name
        self._config_format: str | None = config_format

    @property
    def data(self) -> ConfigData:
        return self._data

    @property
    def namespace(self) -> str | None:
        return self._namespace

    @property
    def file_name(self) -> str | None:
        return self._file_name

    @property
    def config_format(self) -> str | None:
        return self._config_format

    @abstractmethod
    def save(
            self,
            config_pool: ABCConfigPool,
            namespace: str | None = None,
            file_name: str | None = None,
            config_format: str | None = None,
            *processor_args,
            **processor_kwargs
    ) -> None:
        """
        保存配置到文件系统

        :param config_pool: 配置池
        :type config_pool: ABCConfigPool
        :param namespace: 文件命名空间
        :type namespace: Optional[str]
        :param file_name: 文件名
        :type file_name: Optional[str]
        :param config_format: 配置文件的格式
        :type config_format: Optional[str]

        :raise UnsupportedConfigFormatError: 不支持的配置格式
        """

    @classmethod
    @abstractmethod
    def load(
            cls,
            config_pool: ABCConfigPool,
            namespace: str,
            file_name: str,
            config_format: str,
            *processor_args,
            **processor_kwargs
    ) -> Self:
        """
        从文件系统加载配置

        :param config_pool: 配置池
        :type config_pool: ABCConfigPool
        :param namespace: 文件命名空间
        :type namespace: str
        :param file_name: 文件名
        :type file_name: str
        :param config_format: 配置文件的格式
        :type config_format: str

        :return: 配置对象
        :rtype: Self

        :raise UnsupportedConfigFormatError: 不支持的配置格式
        """

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        for field in ["_config_format", "_data", "_namespace", "_file_name"]:
            if getattr(self, field) != getattr(other, field):
                return False
        return True

    def __repr__(self):
        fmt_str: list[str] = []
        for field in ["_config_format", "_data", "_namespace", "_file_name"]:
            field_value = getattr(self, field)
            if field_value is None:
                continue

            fmt_str.append(f"{field[1:]}={field_value!r}")

        return f"{self.__class__.__name__}({", ".join(fmt_str)})"


SLArgument = Sequence | Mapping | tuple[Sequence, Mapping[str, Any]]
C = TypeVar("C", bound=ABCConfig)


class ABCConfigSL(ABC):
    """
    配置文件SaveLoad管理器抽象类
    """

    def __init__(
            self,
            s_arg: SLArgument = None,
            l_arg: SLArgument = None,
            *,
            create_dir: bool = True,
    ):
        """
        :param s_arg: 保存器默认参数
        :type s_arg: Sequence | Mapping | tuple[Sequence, Mapping[str, Any]]
        :param l_arg: 加载器默认参数
        :type l_arg: Sequence | Mapping | tuple[Sequence, Mapping[str, Any]]
        :param create_dir: 是否允许创建目录
        :type create_dir: bool
        """

        def _build_arg(value: SLArgument) -> tuple[list, dict[str, Any]]:
            if value is None:
                return [], {}
            if isinstance(value, Sequence):
                return list(value), {}
            if isinstance(value, Mapping):
                return [], dict(value)
            raise TypeError(f"Invalid argument type, must be '{SLArgument}'")

        self.save_arg: tuple[list, dict[str, Any]] = _build_arg(s_arg)
        self.load_arg: tuple[list, dict[str, Any]] = _build_arg(l_arg)

        self.create_dir = create_dir

    @property
    @abstractmethod
    def regName(self) -> str:
        """
        :return: SL处理器的注册名
        """

    @property
    @abstractmethod
    def fileExt(self) -> list[str]:
        """
        :return: 支持的文件扩展名
        """

    def registerTo(self, config_pool: ABCConfigPool = None) -> None:
        """
        注册到配置池中

        :param config_pool: 配置池，默认为DefaultConfigPool
        :type :type config_pool: ABCConfigPool
        """
        if config_pool is None:
            config_pool = DefaultConfigPool

        config_pool.SLProcessor[self.regName] = self
        for ext in self.fileExt:
            if ext not in config_pool.FileExtProcessor:
                config_pool.FileExtProcessor[ext] = {self.regName}
                continue
            config_pool.FileExtProcessor[ext].add(self.regName)

    @classmethod
    def enable(cls):
        ...

    @abstractmethod
    def save(
            self,
            config: ABCConfig,
            root_path: str,
            namespace: Optional[str],
            file_name: Optional[str],
            *args,
            **kwargs
    ) -> None:
        """
        保存处理器

        :param config: 待保存配置
        :type config: ABCConfig
        :param root_path: 保存的根目录
        :type root_path: str
        :param namespace: 配置的命名空间
        :type namespace: Optional[str]
        :param file_name: 配置文件名
        :type file_name: Optional[str]

        :return: None
        :rtype: None

        :raise FailedProcessConfigFileError: 处理配置文件失败
        """

    @abstractmethod
    def load(
            self,
            config_cls: type[C],
            root_path: str,
            namespace: Optional[str],
            file_name: Optional[str],
            *args,
            **kwargs
    ) -> C:
        """
        加载处理器

        :param config_cls: 配置类
        :type config_cls: type[C]
        :param root_path: 保存的根目录
        :type root_path: str
        :param namespace: 配置的命名空间
        :type namespace: Optional[str]
        :param file_name: 配置文件名
        :type file_name: Optional[str]

        :return: 配置对象
        :rtype: C

        :raise FailedProcessConfigFileError: 处理配置文件失败
        """

    def _getFilePath(
            self,
            config: ABCConfig,
            root_path: str,
            namespace: Optional[str] = None,
            file_name: Optional[str] = None,
    ) -> str:
        """
        获取配置文件对应的文件路径(提供给子类的便捷方法)

        :param config: 配置对象
        :type config: ABCConfig
        :param root_path: 保存的根目录
        :type root_path: str
        :param namespace: 配置的命名空间
        :type namespace: Optional[str]
        :param file_name: 配置文件名
        :type file_name: Optional[str]

        :return: 配置文件路径
        :rtype: str

        :raise ValueError: 当 namespace 和 file_name (即便尝试从config读值)都为 None 时
        """
        if namespace is None:
            namespace = config.namespace
        if file_name is None:
            file_name = config.file_name

        if namespace is None or file_name is None:
            raise ValueError("namespace and file_name can't be None")

        full_path = _norm_join(root_path, namespace, file_name)
        if self.create_dir:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

        return full_path


class Config(ABCConfig):
    """
    配置类
    """

    @override
    def save(
            self,
            config_pool: ABCConfigPool,
            namespace: str | None = None,
            file_name: str | None = None,
            config_format: str | None = None,
            *processor_args,
            **processor_kwargs
    ) -> None:

        if config_format is None:
            config_format = self._config_format

        if config_format is None:
            raise UnsupportedConfigFormatError("Unknown")
        if config_format not in config_pool.SLProcessor:
            raise UnsupportedConfigFormatError(config_format)

        return config_pool.SLProcessor[config_format].save(
            self,
            config_pool.root_path,
            namespace,
            file_name,
            *processor_args,
            **processor_kwargs
        )

    @classmethod
    @override
    def load(
            cls,
            config_pool: ABCConfigPool,
            namespace: str,
            file_name: str,
            config_format: str,
            *processor_args,
            **processor_kwargs
    ) -> Self:

        if config_format not in config_pool.SLProcessor:
            raise UnsupportedConfigFormatError(config_format)

        return config_pool.SLProcessor[
            config_format
        ].load(
            cls,
            config_pool.root_path,
            namespace,
            file_name,
            *processor_args,
            **processor_kwargs
        )


class SimpleYamlSL(ABCConfigSL):
    @property
    @override
    def regName(self) -> str:
        return "yaml"

    @property
    @override
    def fileExt(self) -> list[str]:
        return [".yaml"]

    @classmethod
    @override
    def enable(cls):
        """
        pip install pyyaml
        """
        # noinspection PyPackageRequirements, PyUnresolvedReferences
        import yaml
        cls.yaml = yaml

    @override
    def save(
            self,
            config: ABCConfig,
            root_path: str,
            namespace: Optional[str],
            file_name: Optional[str],
            *args,
            **kwargs
    ) -> None:
        new_args = deepcopy(self.save_arg[0])[:len(args)] = args
        new_kwargs = deepcopy(self.save_arg[1]) | kwargs

        file_path = self._getFilePath(config, root_path, namespace, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            try:
                self.yaml.safe_dump(config.data.data, f, *new_args, **new_kwargs)
            except Exception as e:
                raise FailedProcessConfigFileError(e) from e

    @override
    def load(
            self,
            config_cls: type[C],
            root_path: str,
            namespace: Optional[str],
            file_name: Optional[str],
            *args,
            **kwargs
    ) -> C:
        with open(_norm_join(root_path, namespace, file_name), 'r', encoding="utf-8") as f:
            try:
                data = self.yaml.safe_load(f)
            except Exception as e:
                raise FailedProcessConfigFileError(e) from e
        obj = config_cls(ConfigData(data), namespace=namespace, file_name=file_name, config_format=self.regName)

        return obj


class RuamelYamlSL(ABCConfigSL):

    @property
    @override
    def regName(self) -> str:
        return "ruamel_yaml"

    @property
    @override
    def fileExt(self) -> list[str]:
        return [".yaml"]

    @classmethod
    @override
    def enable(cls):
        """
        pip install ruamel.yaml
        """
        # noinspection PyPackageRequirements, PyUnresolvedReferences
        from ruamel.yaml import YAML
        cls.yaml = YAML(typ="rt", pure=True)

    def save(
            self,
            config: ABCConfig,
            root_path: str,
            namespace: Optional[str],
            file_name: Optional[str],
            *args,
            **kwargs
    ) -> None:
        file_path = self._getFilePath(config, root_path, namespace, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            try:
                self.yaml.dump(config.data.data, f)
            except Exception as e:
                raise FailedProcessConfigFileError(e) from e

    def load(
            self,
            config_cls: type[C],
            root_path: str,
            namespace: Optional[str],
            file_name: Optional[str],
            *args,
            **kwargs
    ) -> C:
        with open(_norm_join(root_path, namespace, file_name), 'r', encoding="utf-8") as f:
            try:
                data = self.yaml.load(f)
            except Exception as e:
                raise FailedProcessConfigFileError(e) from e

        obj = config_cls(ConfigData(data), namespace=namespace, file_name=file_name, config_format=self.regName)

        return obj


class JsonSL(ABCConfigSL):

    @property
    @override
    def regName(self) -> str:
        return "json"

    @property
    @override
    def fileExt(self) -> list[str]:
        return [".json"]

    @classmethod
    @override
    def enable(cls):
        import json
        cls.json = json

    @override
    def save(
            self,
            config: ABCConfig,
            root_path: str,
            namespace: Optional[str],
            file_name: Optional[str],
            *args,
            **kwargs
    ) -> None:
        new_args = deepcopy(self.save_arg[0])[:len(args)] = args
        new_kwargs = deepcopy(self.save_arg[1]) | kwargs

        file_path = self._getFilePath(config, root_path, namespace, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            try:
                self.json.dump(config.data.data, f, *new_args, **new_kwargs)
            except Exception as e:
                raise FailedProcessConfigFileError(e) from e

    @override
    def load(
            self,
            config_cls: type[C],
            root_path: str,
            namespace: Optional[str],
            file_name: Optional[str],
            *args,
            **kwargs
    ) -> C:
        new_args = deepcopy(self.load_arg[0])[len(args)] = args
        new_kwargs = deepcopy(self.load_arg[1]) | kwargs

        with open(_norm_join(root_path, namespace, file_name), "r", encoding="utf-8") as f:
            try:
                data = self.json.load(f, *new_args, **new_kwargs)
            except Exception as e:
                raise FailedProcessConfigFileError(e) from e

        obj = config_cls(ConfigData(data), namespace=namespace, file_name=file_name, config_format=self.regName)

        return obj


class ConfigPool(ABCConfigPool):
    """
    配置池
    """

    def __init__(self, root_path="./.config"):
        super().__init__(root_path)
        self._configs: dict[str, dict[str, ABCConfig]] = {}

    def get(self, namespace: str, file_name: Optional[str] = None) -> dict[str, ABCConfig] | ABCConfig | None:
        """
        获取配置

        如果配置不存在则返回None

        :param namespace: 命名空间
        :type namespace: str
        :param file_name: 文件名
        :type file_name: Optional[str]

        :return: 配置
        :rtype: dict[str, ABCConfig] | ABCConfig | None
        """
        if namespace not in self._configs:
            return None
        result = self._configs[namespace]

        if file_name is None:
            return result

        if file_name in result:
            return result[file_name]

        return None

    def set(self, namespace: str, file_name: str, config: ABCConfig) -> None:
        """
        设置配置

        :param namespace: 命名空间
        :type namespace: str
        :param file_name: 文件名
        :type file_name: str
        :param config: 配置
        :type config: ABCConfig

        :return: None
        :rtype: None
        """
        if namespace not in self._configs:
            self._configs[namespace] = {}

        self._configs[namespace][file_name] = config

    def saveAll(self, ignore_err: bool = False) -> None | dict[str, dict[str, tuple[ABCConfig, Exception]]]:
        """
        保存所有配置

        :param ignore_err: 是否忽略保存导致的错误
        :type ignore_err: bool

        :return: ignore_err为True时返回{Namespace: {FileName: (ConfigObj, Exception)}}，否则返回None
        :rtype: None | dict[str, dict[str, tuple[ABCConfig, Exception]]]
        """
        errors = {}
        for namespace, configs in self._configs.items():
            errors[namespace] = {}
            for file_name, config in configs.items():
                try:
                    config.save(self)
                except Exception as e:
                    if not ignore_err:
                        raise
                    errors[namespace][file_name] = (config, e)

        if not ignore_err:
            return None

        return {k: v for k, v in errors.items() if v}

    def requireConfig(
            self,
            namespace: str,
            file_name: str,
            required: list[str] | dict[str, Any],
            *args,
            **kwargs,
    ):
        """
        获取配置

        :param namespace: 命名空间
        :type namespace: str
        :param file_name: 文件名
        :type file_name: str
        :param required: 必须的配置
        :type required: list[str] | dict[str, Any]
        :param args: 详见RequireConfigDecorator.__init__
        :param kwargs: 详见RequireConfigDecorator.__init__

        :return: RequireConfigDecorator
        :rtype: RequireConfigDecorator
        """
        return RequireConfigDecorator(self, namespace, file_name, RequiredKey(required), *args, **kwargs)

    def __getitem__(self, item):
        return deepcopy(self.configs[item])

    @property
    def configs(self):
        return deepcopy(self._configs)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.configs!r})"


class RequireConfigDecorator:
    """
    装饰器，用于获取配置
    """

    def __init__(
            self,
            config_pool: ConfigPool,
            namespace: str,
            raw_file_name: str,
            required: RequiredKey,
            *,
            config_cls: type[ABCConfig] = Config,
            config_format: Optional[str] = None,
            cache_config: Optional[Callable[[Callable], Callable]] = None,
            allow_create: bool = True,
            filter_kwargs: Optional[dict[str, Any]] = None
    ):
        """
        :param config_pool: 所在的配置池
        :type config_pool: ConfigPool
        :param namespace: 命名空间
        :type namespace: str
        :param raw_file_name: 源文件名
        :type raw_file_name: str
        :param required: 需求的键
        :type required: RequiredKey
        :param config_format: 配置文件格式
        :type config_format: Optional[str]
        :param cache_config: 缓存配置的装饰器，默认为None，即不缓存
        :type cache_config: Optional[Callable[[Callable], Callable]]
        :param allow_create: 是否允许在文件不存在时新建文件
        :type allow_create: bool
        :param filter_kwargs: RequiredKey.filter要绑定的默认参数，默认为allow_create=True
        :type filter_kwargs: dict[str, Any]

        :raise UnsupportedConfigFormatError: 不支持的配置格式
        """
        format_set: set[str]
        if config_format is None:
            _, config_format = os.path.splitext(raw_file_name)
            if not config_format:
                raise UnsupportedConfigFormatError("Unknown")
            if config_format not in config_pool.FileExtProcessor:
                raise UnsupportedConfigFormatError(config_format)
            format_set = config_pool.FileExtProcessor[config_format]
        else:
            format_set = {config_format, }

        def _load_config(format_: str) -> ABCConfig:
            if format_ not in config_pool.SLProcessor:
                raise UnsupportedConfigFormatError(format_)

            result: ABCConfig | None = config_pool.get(namespace, raw_file_name)
            if result is None:
                try:
                    result = config_cls.load(config_pool, namespace, raw_file_name, format_)
                except FileNotFoundError:
                    if not allow_create:
                        raise
                    result = config_cls(
                        ConfigData(),
                        namespace=namespace,
                        file_name=raw_file_name,
                        config_format=format_
                    )

                config_pool.set(namespace, raw_file_name, result)
            return result

        errors = {}
        for f in format_set:
            try:
                ret = _load_config(f)
            except FailedProcessConfigFileError as err:
                errors[f] = err
                continue
            config: ABCConfig = ret
            break
        else:
            raise FailedProcessConfigFileError(errors)

        if filter_kwargs is None:
            filter_kwargs = {}

        self._config: ABCConfig = config
        self._required = required
        self._filter_kwargs = {"allow_create": True} | filter_kwargs
        self._cache_config: Callable = cache_config if cache_config is not None else lambda x: x

    def checkConfig(self, *, ignore_cache: bool = False, **filter_kwargs) -> Any:
        """
        手动检查配置

        :param ignore_cache: 是否忽略缓存
        :type ignore_cache: bool
        :param filter_kwargs: RequiredConfig.filter的参数
        :return: 得到的配置数据
        :rtype: Any
        """
        kwargs = self._filter_kwargs | filter_kwargs
        if ignore_cache:
            return self._required.filter(self._config.data, **kwargs)
        return self._wrapped_filter(**kwargs)

    def __call__(self, func):
        if _is_method(func):
            processor = self._method_processor
        else:
            processor = self._function_processor

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*processor(*args), **kwargs)

        return wrapper

    def _wrapped_filter(self, **kwargs):
        return self._cache_config(self._required.filter(self._config.data, **kwargs))

    def _function_processor(self, *args):
        return self._wrapped_filter(**self._filter_kwargs), *args

    def _method_processor(self, obj, *args):
        return obj, self._wrapped_filter(**self._filter_kwargs), *args


DefaultConfigPool = ConfigPool()
requireConfig = DefaultConfigPool.requireConfig

__all__ = (
    "RequiredKeyNotFoundError",
    "ConfigDataTypeError",
    "UnsupportedConfigFormatError",
    "FailedProcessConfigFileError",

    "ConfigData",
    "RequiredKey",
    "ABCConfig",
    "ABCConfigSL",
    "Config",
    "SimpleYamlSL",
    "RuamelYamlSL",
    "JsonSL",
    "ConfigPool",
    "RequireConfigDecorator",

    "DefaultConfigPool",
    "requireConfig",
)
