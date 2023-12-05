<div align="center">

# StarBotExecutor

[![PyPI](https://img.shields.io/pypi/v/starbot-executor)](https://pypi.org/project/starbot-executor)
[![Python](https://img.shields.io/badge/python-3.10%20|%203.11-blue)](https://www.python.org)
[![License](https://img.shields.io/github/license/Starlwr/StarBotExecutor)](https://github.com/Starlwr/StarBotExecutor/blob/master/LICENSE)
[![STARS](https://img.shields.io/github/stars/Starlwr/StarBotExecutor?color=yellow&label=Stars)](https://github.com/Starlwr/StarBotExecutor/stargazers)

**一个基于订阅发布模式的异步执行器**
</div>

## 特性

* 基于订阅发布模式，实现逻辑解耦
* 分级消息主题，使用灵活

## 快速开始
### 安装

```shell
pip install starbot-executor
```

### 代码框架

引入异步任务执行器 executor，执行初始化操作后即可使用

```python
from starbot_executor import executor

async def main():
    # 业务逻辑
    pass

loop = executor.init()
loop.run_until_complete(main())
loop.run_forever()
```

### 分级消息主题

消息主题为层级结构，较高层级的消息主题可同时监听到较低层级的事件，举例如下：  

使用 **@executor.on()** 装饰的方法，可监听到所有事件  
使用 **@executor.on("Message")** 装饰的方法，可监听到一级消息主题为 Message 的所有事件  
使用 **@executor.on("Message", "Test")** 装饰的方法，可监听到一级消息主题为 Message 且二级消息主题为 Test 的所有事件

### 完整示例

```python
import asyncio
import time

from starbot_executor import executor


async def main():
    # 例 1: 监听默认消息频道所有事件
    @executor.on()
    async def on_all(subjects, event):
        print(f"例 1: {subjects}: {event}")

    # 例 2: 监听默认消息频道一级消息主题为 Message 的所有事件
    @executor.on("Message")
    async def on_message(subjects, event):
        print(f"例 2: {subjects}: {event}")

    # 例 3: 监听默认消息频道一级消息主题为 Message 且二级消息主题为 Test 的所有事件
    @executor.on("Message", "Test")
    async def on_message_test(event):
        print(f"例 3: {event}")

    # 例 4: 监听消息频道为 Private 且一级消息主题为 Message 的所有事件
    @executor.on("Message", channel="Private")
    async def on_message_test():
        print(f"例 4: 私有频道事件")

    # 仅可被例 1 监听到
    executor.dispatch(None, "Other", 1)

    # 可被例 1、2 监听到
    executor.dispatch(None, "Message", "StarBot")

    # 可被例 1、2、3 监听到
    executor.dispatch(None, "Message", "Test")

    # 仅可被例 4 监听到
    executor.dispatch(None, "Message", channel="Private")

    # ——————————————————————————————————————————————————————————————————————

    # 排队执行示例
    await asyncio.sleep(1)
    await executor.create_queue_task(test, 3)
    await executor.create_queue_task(test, 3)
    await executor.create_queue_task(test, 3)


async def test():
    print(f"当前时间戳: {int(time.time())}")


loop = executor.init()
loop.run_until_complete(main())
loop.run_forever()
```

输出结果：
```
例 1: ('Other', 1): None
例 1: ('Message', 'StarBot'): None
例 2: ('Message', 'StarBot'): None
例 1: ('Message', 'Test'): None
例 2: ('Message', 'Test'): None
例 3: None
例 4: 私有频道事件
当前时间戳: 1700658688
当前时间戳: 1700658691
当前时间戳: 1700658694
```

### API 文档

<details>
<summary>点击展开</summary>

#### 1. run
```
run(func: Coroutine) -> Any
```
立即调度异步任务执行，并等待返回  

Args:
* func: 异步任务

Returns:
* 异步任务返回值

#### 2. create_task
```
create_task(self, func: Coroutine) -> Task
```
调度异步任务，不等待返回

Args:
* func: 异步任务

Returns:
* Task，可用于进行 await 操作

#### 3. create_queue_task
```
create_queue_task(self, func: Callable, wait: Union[int, float] = 0) -> NoReturn
```
向异步任务执行队列中添加新任务

Args:
* func: 异步任务
* wait: 执行任务后的等待时间。默认：0

Returns:
* 无返回值

#### 4. remove_queue_task
```
remove_queue_task(self, func: Callable) -> bool
```
从异步任务执行队列中移除任务

Args:
* func: 异步任务

Returns:
* 是否移除成功

#### 5. create_channel
```
create_channel(self, channel: str) -> NoReturn
```
显式创建消息频道，一般情况下可省略，注册事件监听器时若指定了不存在的消息频道会自动创建

Args:
* channel: 消息频道名

Returns:
* 无返回值

#### 6. add_event_listener
```
add_event_listener(self, func: Callable, *subjects: Any, channel: str = "Default") -> NoReturn
```
注册事件监听器

Args:
* func: 回调异步函数
* subjects: 订阅消息主题，可传入多个值
* channel: 注册监听的消息频道。默认：Default

Returns:
* 无返回值

#### 7. remove_event_listener
```
remove_event_listener(self, *subjects: Any, func: Optional[Callable] = None, channel: str = "Default") -> bool
```
移除事件监听器回调函数

Args:
* subjects: 订阅消息主题，可传入多个值
* func: 要移除的回调异步函数，参数为 None 时，移除监听此消息主题的全部回调函数。默认：None
* channel: 移除监听的消息频道。默认：Default

Returns:
* 是否移除成功

#### 8. on
```
on(self, *subjects: Any, channel: str = "Default") -> Callable
```
注册事件监听器装饰器

Args:
* subjects: 订阅消息主题，可传入多个值
* channel: 注册监听的消息频道。默认：Default

Returns:
* 装饰后的函数

#### 9. dispatch
```
dispatch(self, data: Any, *subjects: Any, recursion: bool = True, channel: str = "Default") -> NoReturn
```
发布消息主题

Args:
* data: 事件附加数据
* subjects: 要发布的消息主题，可传入多个值
* recursion: 是否同时调用路径中的消息主题监听器。默认：True
* channel: 要发布的消息频道。默认：Default

Returns:
* 无返回值

</details>