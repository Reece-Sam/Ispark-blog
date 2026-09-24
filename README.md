# iSpark Blog API

A backend REST API for managing blog posts for iSpark Inno websites.

The service is built with **FastAPI** and **PostgreSQL** and provides endpoints for creating, updating, publishing, unpublishing, deleting, restoring, and viewing blog posts.

## Technologies Used

* Python
* FastAPI
* PostgreSQL
* Psycopg
* Pydantic
* Uvicorn

## Project Structure

```text
ispark-blog/
│
├── main.py
├── database.py
├── schemas.py
├── routes/
│   ├── __init__.py
│   └── blogs.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Features

### Blog Management

* Create blog posts
* View blog posts
* Update blog posts
* Publish blogs
* Unpublish blogs
* Soft delete blogs
* Restore deleted blogs
* Filter blogs by:

  * Status
  * Creation date
  * Author
  * Deleted status
* Pagination
* Calculate estimated reading time

### Public Blog

* View published blogs
* Search blogs using full-text search
* Filter blogs by tag
* View a single blog
* View related articles

### Tags

* Create tags for a destination
* View tags for a destination
* Prevent duplicate tags within the same destination

## API Base URL

```text
/api/blogs
```

### Blog Management

```text
POST   /api/blogs/{destination}
GET    /api/blogs/{destination}
PATCH  /api/blogs/{blog_id}
DELETE /api/blogs/{blog_id}
```

### Publishing

```text
POST /api/blogs/{blog_id}/publish
POST /api/blogs/{blog_id}/unpublish
POST /api/blogs/{blog_id}/restore
```

### Tags

```text
POST /api/blogs/tags/{destination}
GET  /api/blogs/tags/{destination}
```

### Public Blog

```text
GET /api/blogs/user/{destination}
GET /api/blogs/user/{destination}/{blog_id}
```

## Database

The project uses PostgreSQL.

The main tables are:

* `staff`
* `posts`
* `tags`

The `posts` table stores blog information such as:

* Title
* Header image
* Author
* Content
* Status
* Destination
* Published date
* Created date
* Last updated date
* Deleted status
* Tag

## Setup

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Move into the project:

```bash
cd ispark-blog
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=your_postgresql_database_url
```

Do not commit the `.env` file to GitHub.

### 5. Run the application

```bash
python main.py
```

The API will run at:

```text
http://127.0.0.1:8000
```

## API Documentation

FastAPI automatically provides interactive API documentation.

Open:

```text
http://127.0.0.1:8000/docs
```

You can use Swagger UI to test the API endpoints.

## Example

Create a blog:

```http
POST /api/blogs/devspace
```

Example request:

```json
{
  "title": "My First Blog",
  "content": "This is my first blog post.",
  "author_id": 1,
  "image_url": "https://example.com/image.jpg",
  "status": "draft",
  "tag_id": 1
}
```

Example response:

```json
{
  "status": "success",
  "message": "Blog created successfully",
  "blog_id": 1
}
```

## Search

Public blogs can be searched using the `search` query parameter:

```text
GET /api/blogs/user/devspace?search=technology
```

Pagination can also be used:

```text
GET /api/blogs/user/devspace?page=1&limit=10
```

## Notes

* Blog deletion uses a soft-delete approach.
* Only published blogs are returned through the public blog endpoints.
* Tags belong to a specific destination.
* Reading time is calculated using an average reading speed of 264 words per minute.
* The project uses PostgreSQL full-text search for blog content.

## Author

**iSpark Inno**

Backend API developed using FastAPI and PostgreSQL.
