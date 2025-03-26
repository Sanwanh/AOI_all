from roboflow import Roboflow
rf = Roboflow(api_key="8b47CuZyeVhRxFXEEbtM")
project = rf.workspace("national-kaohsiung-university-of-science-and-technology-i3169").project("waferbad")
version = project.version(1)
dataset = version.download("coco")