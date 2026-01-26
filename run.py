import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
	"""
    获取资源绝对路径。
    打包后，临时文件会被解压到 sys._MEIPASS 中。
    """
	if getattr(sys, "frozen", False):
		basedir = sys._MEIPASS
	else:
		basedir = os.path.dirname(__file__)
	return os.path.join(basedir, path)

if __name__ == "__main__":
	# 1. 获取 app.py 的绝对路径（打包在exe内部）
	app_path = resolve_path("app.py")

	# 2. 构造模拟的命令行参数
	# "streamlit run app.py --global.developmentMode=false"
	sys.argv = [
		"streamlit",
		"run",
		app_path,
		"--global.developmentMode=false",
	]

	# 3. 启动 Streamlit
	sys.exit(stcli.main())