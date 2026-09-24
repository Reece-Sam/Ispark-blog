import re


from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from psycopg.rows import dict_row

from database import get_connection
from schemas import BlogCreate, TagCreate, BlogUpdate


router = APIRouter(prefix="/api/blogs")


@router.post("/{destination}")
def create_blog(destination: str, blog: BlogCreate):

    connection = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM tags
            WHERE id = %s
              AND destination = %s
        """, (blog.tag_id, destination))

        tag = cursor.fetchone()

        if not tag:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Tag does not belong to this destination"
                }
            )

        cursor.execute("""
            INSERT INTO posts (
                title,
                header_image,
                author_id,
                content,
                status,
                destination,
                tag_id,
                published_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s,
                    CASE WHEN %s = 'published'
                         THEN CURRENT_TIMESTAMP
                         ELSE NULL
                    END)
            RETURNING id
        """, (
            blog.title,
            blog.image_url,
            blog.author_id,
            blog.content,
            blog.status,
            destination,
            blog.tag_id,
            blog.status
        ))

        blog_id = cursor.fetchone()[0]

        connection.commit()

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "message": "Blog created successfully",
            "blog_id": blog_id
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )


@router.get("/{destination}")
def get_blogs(
    destination: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    status: str = Query(None),
    created_at: str = Query(None),
    created_by: int = Query(None),
    is_deleted: bool = Query(None)
):

    connection = None

    try:
        connection = get_connection(row_factory=dict_row)
        cursor = connection.cursor()

        offset = (page - 1) * limit

        query = """
            SELECT
                p.id AS blog_id,
                p.title,
                p.header_image,
                p.content,
                p.author_id,
                s.name AS author_name,
                p.destination,
                p.created_at,
                p.last_updated_at,
                p.status,
                p.published_at,
                p.is_deleted,
                p.deleted_at,
                p.tag_id
            FROM posts p
            JOIN staff s
                ON p.author_id = s.id
            WHERE p.destination = %s
        """

        parameters = [destination]

        if status:
            query += """
                AND p.status = %s
            """
            parameters.append(status)

      
        if created_at:
            query += """
                AND DATE(p.created_at) = %s
            """
            parameters.append(created_at)


        if created_by:
            query += """
                AND p.author_id = %s
            """
            parameters.append(created_by)

        
        if is_deleted is not None:
            query += """
                AND p.is_deleted = %s
            """
            parameters.append(is_deleted)

        query += """
            ORDER BY p.created_at DESC
            LIMIT %s OFFSET %s
        """

        parameters.extend([limit, offset])

        cursor.execute(query, parameters)

        blogs = []

        for row in cursor.fetchall():

            clean_content = re.sub(r"<[^>]+>", "", row["content"])
            clean_content = re.sub(r"[*_#`~]", "", clean_content)

            words = len(clean_content.split())
            reading_time = round(words / 264, 1)

            blogs.append({
                "blog_id": row["blog_id"],
                "title": row["title"],
                "image_url": row["header_image"],
                "content": row["content"],
                "author_id": row["author_id"],
                "author_name": row["author_name"],
                "destination": row["destination"],
                "created_at": row["created_at"],
                "last_updated_at": row["last_updated_at"],
                "status": row["status"],
                "published_at": row["published_at"],
                "is_deleted": row["is_deleted"],
                "deleted_at": row["deleted_at"],
                "tag_id": row["tag_id"],
                "reading_time": reading_time
            })

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "blogs": blogs
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )


@router.patch("/{blog_id}")
def update_blog(blog_id: int, blog: BlogUpdate):

    connection = None

    try:
        connection = get_connection(row_factory=dict_row)
        cursor = connection.cursor()

        # Check if blog exists
        cursor.execute("""
            SELECT
                id,
                title,
                content,
                header_image,
                status,
                tag_id,
                destination,
                is_deleted
            FROM posts
            WHERE id = %s
        """, (blog_id,))

        existing_blog = cursor.fetchone()

        if not existing_blog:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "fail",
                    "message": "Blog not found"
                }
            )

        if existing_blog["is_deleted"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Cannot update a deleted blog"
                }
            )

        if blog.status is not None:

            if blog.status not in ["draft", "published"]:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "fail",
                        "message": "Status must be draft or published"
                    }
                )

        if blog.tag_id is not None:

            cursor.execute("""
                SELECT id
                FROM tags
                WHERE id = %s
                  AND destination = %s
            """, (
                blog.tag_id,
                existing_blog["destination"]
            ))

            tag = cursor.fetchone()

            if not tag:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "fail",
                        "message": "Tag does not belong to this destination"
                    }
                )

        title = blog.title if blog.title is not None else existing_blog["title"]

        content = (
            blog.content
            if blog.content is not None
            else existing_blog["content"]
        )

        image_url = (
            blog.image_url
            if blog.image_url is not None
            else existing_blog["header_image"]
        )

        status = (
            blog.status
            if blog.status is not None
            else existing_blog["status"]
        )

        tag_id = (
            blog.tag_id
            if blog.tag_id is not None
            else existing_blog["tag_id"]
        )

        cursor.execute("""
            UPDATE posts
            SET
                title = %s,
                content = %s,
                header_image = %s,
                status = %s,
                tag_id = %s,
                last_updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        """, (
            title,
            content,
            image_url,
            status,
            tag_id,
            blog_id
        ))

        updated_blog = cursor.fetchone()

        connection.commit()

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "message": "Blog updated successfully",
            "blog_id": updated_blog["id"]
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )


@router.delete("/{blog_id}")
def delete_blog(blog_id: int):

    connection = None

    try:
        connection = get_connection(row_factory=dict_row)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, is_deleted, status
            FROM posts
            WHERE id = %s
        """, (blog_id,))

        blog = cursor.fetchone()

        if not blog:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "fail",
                    "message": "Blog not found"
                }
            )

        if blog["is_deleted"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Blog is already deleted"
                }
            )

        if blog["status"] == "published":
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Unpublish the blog before deleting it"
                }
            )

        cursor.execute("""
            UPDATE posts
            SET
                is_deleted = TRUE,
                deleted_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (blog_id,))

        connection.commit()

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "message": "Blog deleted successfully",
            "blog_id": blog_id
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )


@router.post("/{blog_id}/restore")
def restore_blog(blog_id: int):

    connection = None

    try:
        connection = get_connection(row_factory=dict_row)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, is_deleted
            FROM posts
            WHERE id = %s
        """, (blog_id,))

        blog = cursor.fetchone()

        if not blog:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "fail",
                    "message": "Blog not found"
                }
            )

        if not blog["is_deleted"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Blog is not deleted"
                }
            )

        cursor.execute("""
            UPDATE posts
            SET
                is_deleted = FALSE,
                deleted_at = NULL
            WHERE id = %s
        """, (blog_id,))

        connection.commit()

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "message": "Blog restored successfully",
            "blog_id": blog_id
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )


@router.post("/{blog_id}/publish")
def publish_blog(blog_id: int):

    connection = None

    try:
        connection = get_connection(row_factory=dict_row)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, status, is_deleted, header_image
            FROM posts
            WHERE id = %s
        """, (blog_id,))

        blog = cursor.fetchone()

        if not blog:
            return JSONResponse(
                status_code=404,
                content={ # Filter by deleted status
                    "status": "fail",
                    "message": "Blog not found"
                }
            )

        if blog["is_deleted"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Cannot publish a deleted blog"
                }
            ) # Filter by deleted status

        if blog["status"] == "published":
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Blog is already published"
                }
            )

        if not blog["header_image"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Image is required before publishing"
                }
            )

        cursor.execute("""
            UPDATE posts
            SET
                status = 'published',
                published_at = CURRENT_TIMESTAMP,
                last_updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (blog_id,))

        connection.commit()

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "message": "Blog published successfully",
            "blog_id": blog_id
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )

    
@router.post("/{blog_id}/unpublish")
def unpublish_blog(blog_id: int):

    connection = None

    try:
        connection = get_connection(row_factory=dict_row)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, status, is_deleted
            FROM posts
            WHERE id = %s
        """, (blog_id,))

        blog = cursor.fetchone()

        if not blog:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "fail",
                    "message": "Blog not found"
                }
            )

        if blog["is_deleted"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Cannot unpublish a deleted blog"
                }
            )

        if blog["status"] != "published":
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Blog is not published"
                }
            )

        cursor.execute("""
            UPDATE posts
            SET
                status = 'draft',
                published_at = NULL,
                last_updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (blog_id,))

        connection.commit()

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "message": "Blog unpublished successfully",
            "blog_id": blog_id
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )


# TAGS

@router.post("/tags/{destination}")
def create_tag(destination: str, tag: TagCreate):

    connection = None

    try:
        connection = get_connection(row_factory=dict_row)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id
            FROM tags
            WHERE tag = %s
              AND destination = %s
        """, ((tag.tag, destination)))

        existing_tag = cursor.fetchone()

        if existing_tag:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "fail",
                    "message": "Tag already exists in this destination"
                }
            )

        cursor.execute("""
            INSERT INTO tags (tag, destination)
            VALUES (%s, %s)
            RETURNING id
        """, ((tag.tag, destination)))

        tag_id = cursor.fetchone()["id"]

        connection.commit()

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "message": "Tag created successfully",
            "tag_id": tag_id
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )


@router.get("/tags/{destination}")
def get_tags(destination: str):

    connection = None

    try:
        connection = get_connection(row_factory=dict_row)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, tag, destination
            FROM tags
            WHERE destination = %s
            ORDER BY tag ASC
        """, (destination,))

        tags = []

        for tag in cursor.fetchall():
            tags.append({
                "id": tag["id"],
                "tag": tag["tag"],
                "destination": tag["destination"]
            })

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "tags": tags
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )

# public GET endpoint
@router.get("/user/{destination}")
def get_public_blogs(
    destination: str,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
    tag: str = Query(None),
    search: str = Query(None)
):

    connection = None

    try:
        connection = get_connection(row_factory=dict_row)
        cursor = connection.cursor()

        offset = (page - 1) * limit

        base_query = """
            SELECT
                p.id,
                p.title,
                p.header_image,
                p.content,
                p.published_at,
                s.name AS author_name,
                s.title AS author_title
            FROM posts p
            JOIN staff s
                ON p.author_id = s.id
            WHERE p.destination = %s
              AND p.status = 'published'
              AND p.is_deleted = FALSE
              AND p.published_at IS NOT NULL
        """

        parameters = [destination]

        if tag:
            base_query += """
                AND EXISTS (
                    SELECT 1
                    FROM tags t
                    WHERE t.id = p.tag_id
                      AND t.tag = %s
                )
            """
            parameters.append(tag)

        if search:
            base_query += """
                AND to_tsvector(
                    'english',
                    coalesce(p.title, '') || ' ' || coalesce(p.content, '')
                ) @@ plainto_tsquery('english', %s)
            """
            parameters.append(search)

        base_query += """
            ORDER BY p.published_at DESC
            LIMIT %s OFFSET %s
        """

        parameters.extend([limit, offset])

        cursor.execute(base_query, parameters)

        blogs = []

        for row in cursor.fetchall():

            clean_content = re.sub(r"<[^>]+>", "", row["content"])
            clean_content = re.sub(r"[*_#`~]", "", clean_content)

            words = len(clean_content.split())
            reading_time = round(words / 264, 1)

          

            blogs.append({
                "blog_id": row["id"],
                "title": row["title"],
                "image_url": row["header_image"],
                "content": row["content"],
                "author_name": row["author_name"],
                "author_title": row["author_title"],
                "published_at": row["published_at"],
                "reading_time": reading_time
            })

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "blogs": blogs
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )


@router.get("/user/{destination}/{blog_id}")
def get_public_blog(destination: str, blog_id: int):

    connection = None

    try:
        connection = get_connection(row_factory=dict_row)
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.title,
                p.header_image,
                p.content,
                p.published_at,
                p.tag_id,
                s.name AS author_name,
                s.title AS author_title
            FROM posts p
            JOIN staff s
                ON p.author_id = s.id
            WHERE p.id = %s
              AND p.destination = %s
              AND p.status = 'published'
              AND p.is_deleted = FALSE
              AND p.published_at IS NOT NULL
        """, (blog_id, destination))

        blog = cursor.fetchone()

        if not blog:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "fail",
                    "message": "Blog not found"
                }
            )

        cursor.execute("""
            SELECT
                p.id,
                p.title,
                p.header_image,
                p.published_at
            FROM posts p
            WHERE p.destination = %s
              AND p.status = 'published'
              AND p.is_deleted = FALSE
              AND p.published_at IS NOT NULL
              AND p.tag_id = %s
              AND p.id != %s
            ORDER BY p.published_at DESC
            LIMIT 3
        """, (
            destination,
            blog["tag_id"],
            blog_id
        ))

        related_rows = cursor.fetchall()

        words = len(blog["content"].split())
        reading_time = round(words / 264, 1)

        related_articles = []

        for row in related_rows:
            related_articles.append({
                "blog_id": row["id"],
                "title": row["title"],
                "image_url": row["header_image"],
                "published_at": row["published_at"]
            })

        cursor.close()
        connection.close()

        return {
            "status": "success",
            "blog": {
                "blog_id": blog["id"],
                "title": blog["title"],
                "image_url": blog["header_image"],
                "content": blog["content"],
                "author_name": blog["author_name"],
                "author_title": blog["author_title"],
                "published_at": blog["published_at"],
                "reading_time": reading_time
            },
            "related_articles": related_articles
        }

    except Exception as e:

        if connection:
            connection.rollback()
            connection.close()

        return JSONResponse(
            status_code=500,
            content={
                "status": "fail",
                "message": str(e)
            }
        )