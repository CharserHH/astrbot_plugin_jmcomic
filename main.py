from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from jmcomic import *

@register("jmcomic", "Charser", "一个用于获取漫画信息的插件", "1.0.0")
class MyPlugin(Star):
    help_msg = "使用方式: /jm <漫画ID>"
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
    
    # 注册指令的装饰器。指令名为 jm。
    @filter.command("jm")
    async def jm(self, event: AstrMessageEvent):
        """这是 JMComic 指令 将会获取漫画信息"""
        user_name = event.get_sender_name()
        try:
            # 检测用户信息中是否有漫画ID 若无则发送帮助信息
            if not event.message_str:
                yield event.plain_result(self.help_msg)
                return
            comic_id = int(event.message_str.strip())
            # 检测漫画ID是否为正整数
            if comic_id <= 0:
                yield event.plain_result("漫画ID必须为正整数。\n" + self.help_msg)
                return
            client = JmOption.default().new_jm_client()
            # 获取章节实体类
            photo: JmPhotoDetail = client.get_photo_detail(comic_id, False)
            # 获取漫画的第一张图片
            image: JmImageDetail = photo[0]
            image_url = image.download_url
            # 发送获取到的图片以及漫画信息
            yield event.chain_result([
                event.make_result().url_image(image_url),
                event.make_result().message(f"漫画名称: {photo.title}\n"+
                                            f"作者: {photo.author}\n" +
                                            f"tag: {photo.tags}\n")
            ])

        except Exception as e:
            # logger.error(f"获取漫画信息失败: {e}")
            yield event.plain_result(f"获取漫画信息失败: {e}\n" + self.help_msg)

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
