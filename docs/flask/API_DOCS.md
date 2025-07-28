
## GET /users



Get all users from the system




**Tags:**`Users`, `Admin`


**Middlewares:** rate_limit







**Param:**


- {number} page.query - Page number for pagination

- {number} limit.query - Number of users per page






**Returns:**


- {object} 200 - Success response with users array

- {object} 400 - Invalid parameters






**Example:**

GET /users?page=1&limit=10





**Author:**

John Doe





**Since:**

v1.0.0





---

## GET /users/<int:user_id>


**Summary:** Get current user profile




**Description:** Returns the currently authenticated user's detailed profile information including preferences and settings.



**Tags:**`Users`


**Middlewares:** auth_required











**Param:**


- {string} user_id.path.required - User ID

- {string} Authorization.header.required - Bearer token






**Returns:**


- {object} 200 - User profile object

- {object} 404 - User not found






**Example:**


- GET /users/123

- Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...






**Security:**

Bearer





**Since:**

v1.2.0





---

## POST /users



Create a new user account




**Tags:**`Users`, `Authentication`


**Middlewares:** rate_limit







**Param:**


- {string} email.body.required - User email address

- {string} password.body.required - User password (min 8 characters)

- {string} name.body.required - Full name

- {string} role.body - User role (default: user)






**Returns:**


- {object} 201 - User created successfully

- {object} 400 - Validation error

- {object} 409 - Email already exists






**Example:**


- POST /users

- {"email": "user@example.com", "password": "securepass", "name": "John Doe"}






**Throws:**


- {ValidationError} When email format is invalid

- {ConflictError} When email already exists






**Author:**

Jane Smith





**Since:**

v1.0.0





**Version:**

1.1.0





---

## PUT /users/<int:user_id>


**Summary:** Update user details



Update user profile information




**Tags:**`Users`, `Profile`, `Admin`


**Middlewares:** auth_required, admin_required









**Param:**


- {string} user_id.path.required - User ID to update

- {string} name.body - Updated name

- {string} email.body - Updated email

- {object} preferences.body - User preferences object






**Returns:**


- {object} 200 - User updated successfully

- {object} 403 - Insufficient permissions

- {object} 404 - User not found






**Example:**


- PUT /users/123

- {"name": "John Updated", "preferences": {"theme": "dark"}}






**Security:**

AdminOnly





**Ratelimit:**

10 requests per minute





**Since:**

v1.1.0





---

## DELETE /orders/<int:order_id>


**Summary:** Delete order permanently




**Description:** Permanently removes an order from the system. This action cannot be undone and will trigger audit logging.



**Tags:**`Orders`, `Admin`, `Audit`


**Middlewares:** admin_required, rate_limit











**Param:**


- {string} order_id.path.required - Order ID to delete

- {string} reason.body - Reason for deletion






**Returns:**


- {object} 200 - Order deleted successfully

- {object} 404 - Order not found






**Example:**


- DELETE /orders/123

- {"reason": "Customer requested cancellation"}






**Deprecated:**

Use PATCH /orders/:id/cancel instead





**Warning:**

This is a destructive operation





**Audit:**

Required - logs deletion with user info





**Author:**

Admin Team





**Since:**

v2.0.0





**Todo:**

Add soft delete option





---

## GET /health



Get system health and status




**Tags:**`System`, `Monitoring`, `Health`


**Middlewares:** None







**Returns:**


- {object} 200 - System status

- {object} 503 - Service unavailable






**Example:**


- GET /health

- Response: {"status": "OK", "uptime": 12345, "version": "1.0.0"}






**Public:**

No authentication required





**Cache:**

30 seconds





**Monitoring:**

Uptime check endpoint





**Sla:**

99.9% availability





---

## GET /api/products


**Summary:** Manage product catalog



Product management endpoints



**Description:** Complete CRUD operations for product management including inventory tracking and catalog updates.



**Tags:**`Products`, `Inventory`, `Catalog`


**Middlewares:** rate_limit











**Param:**


- {string} category.query - Filter by product category

- {boolean} active.query - Filter by active status






**Returns:**

{array} 200 - Array of products





**Example:**

GET /api/products?category=electronics&active=true





**Cache:**

5 minutes





**Ratelimit:**

100 requests per minute





**Version:**

2.1.0





**See:**

/api/categories for available categories





---

## POST /api/products


**Summary:** Manage product catalog



Product management endpoints



**Description:** Complete CRUD operations for product management including inventory tracking and catalog updates.



**Tags:**`Products`, `Inventory`, `Catalog`


**Middlewares:** rate_limit











**Param:**


- {string} category.query - Filter by product category

- {boolean} active.query - Filter by active status






**Returns:**

{array} 200 - Array of products





**Example:**

GET /api/products?category=electronics&active=true





**Cache:**

5 minutes





**Ratelimit:**

100 requests per minute





**Version:**

2.1.0





**See:**

/api/categories for available categories





---

## POST /api/upload


**Summary:** Upload user files



File upload endpoint




**Tags:**`Files`, `Upload`


**Middlewares:** auth_required, rate_limit









**Param:**


- {file} file.formData.required - File to upload

- {string} category.formData - File category






**Returns:**


- {object} 200 - Upload successful

- {object} 413 - File too large






**Example:**

POST /api/upload





**Maxsize:**

10MB





**Formats:**

jpg, png, pdf, docx





**Storage:**

AWS S3





**Retention:**

7 years





---

## GET /api/search


**Summary:** Global search functionality



Search across all resources




**Tags:**`Search`, `Query`


**Middlewares:** rate_limit









**Param:**


- {string} q.query.required - Search query

- {string} type.query - Resource type filter

- {number} page.query - Page number (default: 1)

- {number} per_page.query - Results per page (default: 20)






**Returns:**


- {object} 200 - Search results

- {object} 400 - Invalid query






**Example:**

GET /api/search?q=python&type=users&page=1





**Performance:**

Elasticsearch backend





**Indexing:**

Real-time updates





**Relevance:**

Machine learning scoring





**Analytics:**

Search queries logged





---
