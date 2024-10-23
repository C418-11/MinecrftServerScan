# 一键构建工具

---

## 警告

1. 此工具仅支持`Windows10+`
2. 必须安装`Python3.12`及项目根目录[`requirements[点击跳转]`](../requirements.txt)存储的必要库
3. D盘的构建临时文件夹`$.MSS`目录树会有改动，不要增改目录内容
4. 同上不要增改项目目录下[`..\build_tools\Build[点击跳转]`](Build)的内容
5. 同上构建输出文件夹[`..\dist[点击跳转]`](../dist)的内容在每次构建时会被覆盖，长期使用该构建结果应复制ServerScan文件夹到别处使用

---

## 开始

1. 下载构建所需依赖

   在当前文件夹执行
    ```commandline
    pip install requirements.txt
    ```

2. **_[配置](./BuildConfig.bat)_**
    1. `CONFIG_PYTHON`

       python.exe的位置(一般位于\Scripts\python.exe)
    2. `CONFIG_PYINSTALLER`

       pyinstaller.exe的位置(一般位于\Scripts\pyinstaller.exe)

3. **开始构建**

   执行>>[`这个文件[点击跳转]`](./Build.bat)<<

   或者在当前README所在文件夹使用命令提示符执行:
    ```commandline
    Build
    ```

---

## FAQ

1. 收到提示`Build/pyd, 是否确认(Y/N)?`

   输入`y`(大小写无所谓)并按下`Enter`(也就是回车键)

---

## 高级 (仅供技术人员使用)

1. [`BuildPyd.bat[点击跳转]`](./BuildPyd.bat)

   一键构建默认pyd文件预设

2. [`BuildExe.bat[点击跳转]`](./BuildExe.bat)

   一键将GUI核心打包为exe

3. [`CopyFiles.bat[点击跳转]`](./CopyFiles.bat)

   快速组合所有的构建结果

4. [`CleanBuild.bat[点击跳转]`](./CleanBuild.bat)

   用于清空`$.MSS`中临时文件的脚本