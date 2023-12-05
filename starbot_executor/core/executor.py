import asyncio
import inspect
from asyncio import AbstractEventLoop, Task, Queue
from collections import deque
from typing import Dict, Coroutine, Set, Optional, Any, NoReturn, Tuple, Union, List, Callable


class Handler:
    """
    订阅消息主题回调处理器
    """
    callbacks: List[Callable]
    """消息主题回调方法列表"""

    child: Dict[str, "Handler"]
    """子消息主题"""

    def __init__(self):
        self.callbacks = []
        self.child = {}

    def __contains__(self, item):
        return item in self.child

    def __getitem__(self, key):
        return self.child[key]

    def __setitem__(self, key, value):
        self.child[key] = value

    def __iter__(self):
        return iter(self.callbacks)

    def add(self, callback) -> NoReturn:
        """
        添加回调异步函数

        Args:
            callback: 异步任务
        """
        self.callbacks.append(callback)

    def remove(self, callback) -> bool:
        """
        移除回调异步函数

        Args:
            callback: 异步任务

        Returns:
            是否移除成功
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
            return True
        else:
            return False

    def pop(self, key) -> bool:
        """
        移除子消息主题

        Args:
            key: 要移除的消息主题

        Returns:
            是否移除成功
        """
        if key in self.child:
            self.child.pop(key)
            return True
        else:
            return False


class AsyncTaskExecutor:
    """
    异步任务执行器
    """
    __loop: Optional[AbstractEventLoop]
    """asyncio 事件循环"""

    __running_tasks: Set[Task]
    """执行中的任务"""

    __task_queue: Queue[Tuple[Callable, int]]
    """排队执行队列"""

    __handlers: Dict[str, Handler]
    """订阅-发布回调方法"""

    def __init__(self):
        self.__loop = None
        self.__running_tasks = set()
        self.__task_queue = Queue()
        self.__handlers = {"Default": Handler()}

    def __contains__(self, item):
        return item in list(map(lambda task: task[0], self.__task_queue.__getattribute__("_queue")))

    def init(self, loop: Optional[AbstractEventLoop] = None) -> AbstractEventLoop:
        """
        初始化异步任务执行器

        Args:
            loop: 事件循环，未传入时自动创建新事件循环。默认：None

        Returns:
            使用的事件循环
        """
        self.__loop = loop
        if self.__loop is None:
            self.__loop = asyncio.new_event_loop()
        self.create_task(self.__queue_task_executor())
        return self.__loop

    async def run(self, func: Coroutine) -> Any:
        """
        立即调度异步任务执行，并等待返回

        Args:
            func: 异步任务

        Returns:
            异步任务返回值
        """
        return await self.create_task(func)

    def create_task(self, func: Coroutine) -> Task:
        """
        调度异步任务，不等待返回

        Args:
            func: 异步任务

        Returns:
            Task
        """
        if self.__loop is None:
            raise RuntimeError("在执行任务之前先使用 executor.init() 或 executor.init(loop) 方法初始化异步执行器")

        task = self.__loop.create_task(func)
        self.__running_tasks.add(task)
        task.add_done_callback(lambda t: self.__running_tasks.remove(t))
        return task

    async def create_queue_task(self, func: Callable, wait: Union[int, float] = 0) -> NoReturn:
        """
        向异步任务执行队列中添加新任务

        Args:
            func: 异步任务
            wait: 执行任务后的等待时间。默认：0
        """
        await self.__task_queue.put((func, wait))

    def remove_queue_task(self, func: Callable) -> bool:
        """
        从异步任务执行队列中移除任务

        Args:
            func: 异步任务

        Returns:
            是否移除成功
        """
        if func not in self:
            return False

        async def empty():
            pass

        queue: deque = self.__task_queue.__getattribute__("_queue")
        for index, (task, _) in enumerate(queue):
            if task == func:
                queue[index] = (empty, 0)
                return True

        return False

    async def __queue_task_executor(self) -> NoReturn:
        """
        异步任务队列调度执行器，随异步任务执行器初始化自动启动
        """
        while True:
            func, wait = await self.__task_queue.get()
            self.create_task(func())
            await asyncio.sleep(wait)
            self.__task_queue.task_done()

    def create_channel(self, channel: str) -> NoReturn:
        """
        显式创建消息频道，一般情况下可省略，注册事件监听器时若指定了不存在的消息频道会自动创建

        Args:
            channel: 消息频道名
        """
        if channel not in self.__handlers:
            self.__handlers[channel] = Handler()

    def add_event_listener(self, func: Callable, *subjects: Any, channel: str = "Default") -> NoReturn:
        """
        注册事件监听器

        Args:
            func: 回调异步函数
            subjects: 订阅消息主题，可传入多个值
            channel: 注册监听的消息频道。默认：Default
        """
        if channel not in self.__handlers:
            self.__handlers[channel] = Handler()

        handler = self.__handlers[channel]
        for subject in subjects:
            if subject not in handler:
                handler[subject] = Handler()
            handler = handler[subject]
        handler.add(func)

    def remove_event_listener(self, *subjects: Any, func: Optional[Callable] = None, channel: str = "Default") -> bool:
        """
        移除事件监听器回调函数

        Args:
            subjects: 订阅消息主题，可传入多个值
            func: 要移除的回调异步函数，参数为 None 时，移除监听此消息主题的全部回调函数。默认：None
            channel: 移除监听的消息频道。默认：Default

        Returns:
            是否移除成功
        """
        if channel not in self.__handlers:
            return False

        size = len(subjects)
        handler = self.__handlers[channel]

        for index, subject in enumerate(subjects):
            if index == size - 1:
                if subject in handler:
                    if func is None:
                        return handler.pop(subject)
                    else:
                        handler = handler[subject]
                        return handler.remove(func)
                else:
                    return False
            else:
                if subject in handler:
                    handler = handler[subject]
                else:
                    return False

    def on(self, *subjects: Any, channel: str = "Default") -> Callable:
        """
        注册事件监听器装饰器

        Args:
            subjects: 订阅消息主题，可传入多个值
            channel: 注册监听的消息频道。默认：Default
        """

        def decorator(func: Callable):
            self.add_event_listener(func, *subjects, channel=channel)
            return func

        return decorator

    def dispatch(self, data: Any, *subjects: Any, recursion: bool = True, channel: str = "Default") -> NoReturn:
        """
        发布消息主题

        Args:
            data: 事件附加数据
            subjects: 要发布的消息主题，可传入多个值
            recursion: 是否同时调用路径中的消息主题监听器。默认：True
            channel: 要发布的消息频道。默认：Default
        """
        if channel not in self.__handlers:
            return

        handler = self.__handlers[channel]
        if recursion:
            for callback in handler:
                self.__invoke(callback, data, subjects)

        size = len(subjects)
        for index, subject in enumerate(subjects):
            if subject not in handler:
                return

            handler = handler[subject]
            if recursion or index == size - 1:
                for callback in handler:
                    self.__invoke(callback, data, subjects)

    def __invoke(self, func: Callable, data: Any, subjects: Any) -> NoReturn:
        """
        动态传参方法调用

        Args:
            func: 异步任务
            data: 附加数据
            subjects: 消息主题
        """
        signature = inspect.signature(func)
        parameters_count = len(signature.parameters)
        if parameters_count == 0:
            self.create_task(func())
        elif parameters_count == 1:
            self.create_task(func(data))
        elif parameters_count == 2:
            self.create_task(func(subjects, data))


executor: AsyncTaskExecutor = AsyncTaskExecutor()
