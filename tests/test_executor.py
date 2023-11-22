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
    await executor.create_queue_task(test(), 3)
    await executor.create_queue_task(test(), 3)
    await executor.create_queue_task(test(), 3)


async def test():
    print(f"当前时间戳: {int(time.time())}")


loop = executor.init()
loop.run_until_complete(main())
loop.run_forever()
