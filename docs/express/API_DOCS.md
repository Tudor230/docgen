
## GET /users



Get all users from the system




**Tags:**`Users`, `Admin`


**Middlewares:** None


**Parameters:**


- **page** (number) - Page number for pagination
  - Location: query

- **limit** (number) - Number of users per page
  - Location: query




**Returns:**


- **200** (object) - Success response with users array

- **400** (object) - Invalid parameters













**Example:**

GET /users?page=1&limit=10





**Author:**

John Doe





**Since:**

v1.0.0





---

## GET /users/{id}


**Summary:** Get current user profile




**Description:** Returns the currently authenticated user's detailed profile information including preferences and settings.



**Tags:**`Users`


**Middlewares:** None


**Parameters:**


- **id** (string) *required* - User ID
  - Location: path

- **Authorization** (string) *required* - Bearer token
  - Location: header




**Returns:**


- **200** (object) - User profile object

- **404** (object) - User not found

















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


**Middlewares:** None


**Parameters:**


- **email** (string) *required* - User email address
  - Location: body

- **password** (string) *required* - User password (min 8 characters)
  - Location: body

- **name** (string) *required* - Full name
  - Location: body

- **role** (string) - User role (default: user)
  - Location: body




**Returns:**


- **201** (object) - User created successfully

- **400** (object) - Validation error

- **409** (object) - Email already exists













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

## PUT /users/{id}


**Summary:** Update user details



Update user profile information




**Tags:**`Users`, `Profile`, `Admin`


**Middlewares:** None


**Parameters:**


- **id** (string) *required* - User ID to update
  - Location: path

- **name** (string) - Updated name
  - Location: body

- **email** (string) - Updated email
  - Location: body

- **preferences** (object) - User preferences object
  - Location: body




**Returns:**


- **200** (object) - User updated successfully

- **403** (object) - Insufficient permissions

- **404** (object) - User not found















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

## DELETE /orders/{id}


**Summary:** Delete order permanently




**Description:** Permanently removes an order from the system. This action cannot be undone and will trigger audit logging.



**Tags:**`Orders`, `Admin`, `Audit`


**Middlewares:** None


**Parameters:**


- **id** (string) *required* - Order ID to delete
  - Location: path

- **reason** (string) - Reason for deletion
  - Location: body




**Returns:**


- **200** (object) - Order deleted successfully

- **404** (object) - Order not found

















**Example:**


- DELETE /orders/ord_123

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


- **200** (object) - System status

- **503** (object) - Service unavailable











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

## GET /products


**Summary:** Manage product catalog



Product management endpoints



**Description:** Complete CRUD operations for product management including inventory tracking and catalog updates.



**Tags:**`Products`, `Inventory`, `Catalog`


**Middlewares:** None


**Parameters:**


- **category** (string) - Filter by product category
  - Location: query

- **active** (boolean) - Filter by active status
  - Location: query




**Returns:**


- **200** (array) - Array of products

















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

## POST /products



Create new product




**Tags:**`Products`, `Admin`


**Middlewares:** None


**Parameters:**


- **name** (string) *required* - Product name
  - Location: body

- **price** (number) *required* - Product price
  - Location: body

- **category** (string) *required* - Product category
  - Location: body

- **description** (string) - Product description
  - Location: body




**Returns:**


- **201** (object) - Product created













**Example:**


- POST /api/products

- {"name": "Widget", "price": 29.99, "category": "gadgets"}






**Validation:**

Requires admin role





**Audit:**

Product creation logged





---

## POST /upload


**Summary:** Upload user files



File upload endpoint




**Tags:**`Files`, `Upload`


**Middlewares:** None


**Parameters:**


- **file** (file) *required* - File to upload
  - Location: formData

- **category** (string) - File category
  - Location: formData




**Returns:**


- **200** (object) - Upload successful

- **413** (object) - File too large















**Example:**

POST /upload





**Maxsize:**

10MB





**Formats:**

jpg, png, pdf, docx





**Storage:**

AWS S3





**Virus-Scan:**

Enabled





**Retention:**

7 years





---
