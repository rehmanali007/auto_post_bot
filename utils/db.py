from pymongo import MongoClient


class DB:
    def __init__(self):
        client = MongoClient()
        db = client.postsDB
        self.posts = db.posts

    async def create_post(self, post_title: str,
                          post_desc: str,
                          post_image_location: str = None):
        created_post = self.posts.insert_one({
            'post_title': post_title,
            'post_desc': post_desc,
            'post_image_location': post_image_location
        })
        return created_post.inserted_id

    async def remove_post(self, post_id):
        self.posts.delete_one({'_id': post_id})

    async def get_post(self, post_id):
        post = self.posts.find_one({'_id': post_id})
        return post
