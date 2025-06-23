from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from jmcomic import *
from datetime import datetime
import os

@register("jmcomic", "Charser", "一个用于获取漫画信息的插件", "1.0.0")
class MyPlugin(Star):
    help_msg = "使用方式: /jm <漫画ID>"
    client : JmHtmlClient|JmApiClient = None
    def __init__(self, context: Context):
        super().__init__(context)


    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        self.client = JmOption.default().new_jm_client()

    @filter.command("jm搜索")
    async def jm_search(self, event: AstrMessageEvent):
        """JM搜索指令 使用方式 '/jm搜索 <关键词1> <关键词2>...' 将会获取对应关键词的漫画信息 以时间从新到旧排列"""
        user_name = event.get_sender_name()
        try:
            # 将用户先发送的信息用空格分割
            # 过滤掉指令名，获取用户输入的关键词
            context_str = event.message_str.strip()
            comic_str = context_str.split(" ", 1)

            # 检测用户信息中是否有关键词 若无则发送帮助信息
            if not comic_str or len(comic_str) < 2:
                yield event.plain_result(self.help_msg)
                return
            raw_keywords = comic_str[1].strip()

            # 处理关键词 用空格分割 再用‘ +’组合在一起
            keywords = ' +'.join(raw_keywords.split())

            # 获取漫画搜索结果 page每次迭代返回album_id和title
            page : JmSearchPage = self.client.search_site(keywords, 1)
            # 检测是否有搜索结果
            if not page or page.page_size <= 0:
                yield event.plain_result(f"没有找到与'{raw_keywords}'相关的漫画。\n" + self.help_msg)
                return
            answer_str = f"搜索结果: @{user_name} \n----------\n"
            for album_id, title in page:
                photo: JmPhotoDetail = self.client.get_photo_detail(album_id, False)
                # 组合漫画的相关信息
                answer_str += f"jm号: {album_id}\n标题: {title}\n作者: {photo.author}\n标签: {photo.tags}\n----------\n"
            # 发送搜索结果
            yield event.plain_result(answer_str)

        except Exception as e:
            logger.error(f"搜索漫画失败: {e}")
            yield event.plain_result(f"搜索漫画失败: {e}\n" + self.help_msg)
    
    # 注册指令的装饰器。指令名为 jm。
    @filter.command("jm")
    async def jm(self, event: AstrMessageEvent):
        """JM指令 使用方式'/jm <jm号>' 将会获取对应编号的漫画信息"""
        user_name = event.get_sender_name()
        try:
            # 将用户先发送的信息用空格分割
            # 过滤掉指令名，获取用户输入的漫画ID
            context_str = event.message_str.strip()
            comic_str = context_str.split(" ", 1)

            # 检测用户信息中是否有漫画ID 若无则发送帮助信息
            if not comic_str or len(comic_str) < 2:
                yield event.plain_result(self.help_msg)
                return
            comic_id = int(comic_str[1].strip())
            # 检测漫画ID是否为正整数
            if comic_id <= 0:
                yield event.plain_result("漫画ID必须为正整数。\n" + self.help_msg)
                return
            # 获取章节实体类
            photo: JmPhotoDetail = self.client.get_photo_detail(comic_id, False)
            # 获取漫画的第一张图片
            image: JmImageDetail = photo[0]
            # image_url = image.download_url
            # 依据当前日期时间生成图片名
            image_name = datetime.now().strftime('%Y%m%d%H%M%S') + '.jpg'
            #检测是否有下载目录，如果没有则创建
            if not os.path.exists('./download'):
                os.makedirs('./download')
            self.client.download_by_image_detail(image, './download/' + image_name)
            # 发送获取到的图片以及漫画信息
            # yield event.chain_result([
            #     event.make_result().url_image(image_url),
            #     event.make_result().message(
            #         "获取漫画信息成功!@" + f"{event.get_sender_name()}\n" +
            #         f"漫画名称: {photo.title}\n"+
            #         f"作者: {photo.author}\n" +
            #         f"tag: {photo.tags}\n")
            # ])

            yield event.image_result('./download/' + image_name)
            yield event.plain_result(
                "获取漫画信息成功!@" + f"{user_name}\n" +
                f"漫画名称: {photo.title}\n" +
                f"作者: {photo.author}\n" +
                f"tag: {photo.tags}\n"
            )
            # 清理下载的图片
            os.remove('./download/' + image_name)

        except Exception as e:
            logger.error(f"获取漫画信息失败: {e}")
            yield event.plain_result(f"获取漫画信息失败: {e}\n" + self.help_msg)

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
