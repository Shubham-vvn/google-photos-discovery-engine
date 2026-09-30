"""
Reddit Scraper

Scrapes Myntra and fashion-related discussions, posts, and comments
from relevant subreddits using PRAW.
"""

from datetime import datetime
from typing import Any, Dict, List
import praw
from config.settings import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
from .base_scraper import BaseScraper


class RedditScraper(BaseScraper):
    SUBREDDITS = [
        "googlephotos",
        "google",
        "Android",
        "techsupport",
        "GooglePixel",
    ]
    SEARCH_QUERIES = [
        "google photos search",
        "can't find photo google photos",
        "remember photo google photos",
        "cant find picture google photos",
        "search broken google photos",
        "find receipt google photos",
        "find screenshot google photos",
        "how to find old photo google photos",
        "ask photos search",
        "google photos scroll fatigue",
    ]

    def __init__(self):
        super().__init__(source_name="reddit")
        if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
            self.reddit = praw.Reddit(
                client_id=REDDIT_CLIENT_ID,
                client_secret=REDDIT_CLIENT_SECRET,
                user_agent=REDDIT_USER_AGENT,
            )
        else:
            self.reddit = None

    def scrape(self, limit_per_query: int = 100) -> List[Dict[str, Any]]:
        if not self.reddit:
            print("⚠️ Reddit credentials not set. Skipping Reddit scraper.")
            return []

        documents = []
        seen_ids = set()

        for subreddit_name in self.SUBREDDITS:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                for query in self.SEARCH_QUERIES:
                    try:
                        for post in subreddit.search(query, limit=limit_per_query):
                            if post.id not in seen_ids:
                                seen_ids.add(post.id)
                                doc = self._post_to_document(post)
                                if doc["text"].strip() not in ["[deleted]", "[removed]"]:
                                    documents.append(doc)

                                # Top level comments
                                post.comments.replace_more(limit=0)
                                for comment in post.comments.list()[:20]:
                                    if comment.id not in seen_ids:
                                        seen_ids.add(comment.id)
                                        c_doc = self._comment_to_document(comment, post.id)
                                        if c_doc["text"].strip() not in ["[deleted]", "[removed]"]:
                                            documents.append(c_doc)
                    except Exception as q_err:
                        print(f"⚠️ Error searching r/{subreddit_name} for '{query}': {q_err}")
            except Exception as sub_err:
                print(f"⚠️ Error accessing r/{subreddit_name}: {sub_err}")

        return documents

    def _post_to_document(self, post) -> Dict[str, Any]:
        text = f"{post.title}\n\n{post.selftext}" if post.selftext else post.title
        author_name = str(post.author.name) if post.author else "anonymous"
        timestamp = datetime.utcfromtimestamp(post.created_utc).isoformat() if post.created_utc else None
        return self.create_raw_document(
            raw_item=post,
            text=text,
            source_id=post.id,
            author=author_name,
            metadata={
                "subreddit": str(post.subreddit),
                "upvotes": post.score,
                "num_comments": post.num_comments,
                "timestamp": timestamp,
                "post_type": "submission",
            },
        )

    def _comment_to_document(self, comment, parent_post_id: str) -> Dict[str, Any]:
        author_name = str(comment.author.name) if comment.author else "anonymous"
        timestamp = datetime.utcfromtimestamp(comment.created_utc).isoformat() if comment.created_utc else None
        return self.create_raw_document(
            raw_item=comment,
            text=comment.body,
            source_id=comment.id,
            author=author_name,
            metadata={
                "subreddit": str(comment.subreddit),
                "upvotes": comment.score,
                "timestamp": timestamp,
                "post_type": "comment",
                "reply_to": parent_post_id,
            },
        )

    def get_source_id(self, raw_item: Any) -> str:
        return str(raw_item.id)
