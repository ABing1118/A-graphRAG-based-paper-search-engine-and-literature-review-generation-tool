# 项目简单说明（中文版）

该项目本身的设计初衷是为了设计一款能够提高‘学术研究人员进行论文查询和总结’的效率的软件，通过结合现代搜索引擎的基本功能，外加提供citation network的展示，以及literature review的生成来达到让研究人员快速，直观地得到当前query领域的研究情况和引文网络，项目本身为毕设级别，创新点在于literature review的生成流程由LLM主导，结合graphRAG技术来实现高质量的literature review的生成。

由于本项目仅仅是毕设级别，并未打算投入生产或盈利使用，所以LLM的参数以及数据库的设计相对来说并不是最佳状态，LLM采用7b的模型，数据库采用本地缓存的形式，后续如果硬件设备支持更高质量的模型可以采用更高参数的模型。

# 代码说明

本项目把前端后端的代码进行了分离（但仍在一个项目内）

### 本地后端启动方式：

cd到项目backend文件夹下

创建一个虚拟环境，本项目用的python version == 3.10

安装依赖，执行：

```bash
pip install -r requirements.txt
```

如果有没有装好的依赖报错了pip装一下就行

运行fastAPI的本地后端服务：

```bash
uvicorn main:app --reload --port 8000
```

### 前端启动方式：

新建一个终端

cd到frontend文件夹下

```bash
npm install 安装依赖
```

运行前端代码：

```bash
npm start
```

### 服务端启动方式可以看以下项目的readme

https://github.com/ABing1118/A-graphRAG-based-paper-search-engine-and-literature-review-generation-tool-Code-on-jupyter-server-

只有三部分全都不报错启动之后，项目才算可以运行
