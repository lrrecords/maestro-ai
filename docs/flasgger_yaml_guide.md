# Flasgger YAML Best Practices Guide
*Writing OpenAPI/Swagger documentation blocks inside Python docstrings*

---

## 1. Indentation Rules

- **Always use spaces — never tabs.** YAML parsers (including PyYAML, which Flasgger uses) reject tab characters.
- **2 spaces per indentation level** is the Flasgger/Swagger convention. Some editors default to 4; override them.
- The YAML block begins **immediately after the opening `"""`** or on the next line — but must be consistently aligned relative to itself, not the Python code.
- Flasgger strips leading whitespace based on the **first non-empty line** of the docstring. Align everything relative to that anchor line.

```
def my_view():
    """
    Summary line here.
    ---
    tags:
      - Users          # 2 spaces
    parameters:
      - name: user_id  # 2 spaces
        in: query      # 4 spaces (nested under parameters item)
        type: string   # 4 spaces
    responses:
      200:             # 2 spaces
        description: OK
    """
```

> ⚠️ The `---` separator is **required** by Flasgger. Everything before it is treated as the human-readable summary and ignored by the parser.

---

## 2. Minimal Valid Parameters Blocks

### Query Parameter

```yaml
parameters:
  - name: search
    in: query
    type: string
    required: false
    description: Search term to filter results.
```

### Body Parameter (Swagger 2.0 style — what Flasgger uses by default)

```yaml
parameters:
  - name: body
    in: body
    required: true
    schema:
      type: object
      required:
        - username
      properties:
        username:
          type: string
          example: brett_records
        email:
          type: string
          format: email
          example: brett@lrrecords.com
```

> ⚠️ You can only have **one** `in: body` parameter per endpoint. Multiple body fields go inside `schema.properties`, not as separate parameters.

---

## 3. Field Order and Required vs Optional

Swagger 2.0 does not enforce field ordering, but consistency aids readability. Recommended order:

### Parameter fields

| Field | Required? | Notes |
|---|---|---|
| `name` | ✅ Required | Must match actual query key or body field |
| `in` | ✅ Required | `query`, `body`, `path`, `header`, or `formData` |
| `type` | ✅ (non-body) | Omit for `in: body`; use `schema` instead |
| `required` | Optional | Defaults to `false` |
| `description` | Optional | Strongly recommended |
| `default` | Optional | Shown in Swagger UI |
| `example` | Optional | Shown in Swagger UI (inside `schema` for body) |
| `enum` | Optional | Restricts allowed values |
| `format` | Optional | e.g. `email`, `date`, `int64`, `uuid` |
| `schema` | Body only | Contains `type`, `properties`, `required` |

### Response fields

| Field | Required? | Notes |
|---|---|---|
| HTTP status code | ✅ Required | e.g. `200`, `400`, `422` |
| `description` | ✅ Required | Even a single word satisfies the spec |
| `schema` | Optional | Define the shape of the response body |
| `examples` | Optional | Provide sample response payloads |

### Top-level docstring fields

| Field | Required? | Notes |
|---|---|---|
| `tags` | Optional | Groups endpoints in the Swagger UI sidebar |
| `summary` | Optional | Short title (Flasgger uses the pre-`---` text if omitted) |
| `description` | Optional | Long-form markdown description |
| `operationId` | Optional | Must be unique if used |
| `consumes` | Optional | Defaults to `application/json` |
| `produces` | Optional | Defaults to `application/json` |
| `parameters` | Optional | Omit if endpoint takes no input |
| `responses` | ✅ Required | At minimum define the success case |

---

## 4. Common Pitfalls

### ❌ Tabs instead of spaces
```yaml
parameters:
	- name: id   # TAB character — will raise a YAML parse error
```

### ❌ Inconsistent indentation
```yaml
parameters:
  - name: id
      in: query   # Extra indent breaks the mapping
```

### ❌ Missing `---` separator
```python
def view():
    """
    tags:           # Flasgger will ignore this entirely
      - Widgets
    """
```

### ❌ Trailing whitespace
Trailing spaces after values are valid YAML but cause subtle bugs (especially in `description` strings). Configure your editor to strip them on save.

### ❌ Empty fields with no value
```yaml
description:        # Null value — fine in YAML but Swagger UI may render oddly
description: ""     # Better: explicit empty string
```
Just omit optional fields entirely if you have nothing to say.

### ❌ Multiple `in: body` parameters
```yaml
parameters:
  - name: username
    in: body         # ✅
  - name: email
    in: body         # ❌ — Swagger 2.0 allows only one body param
```
Combine them under a single body parameter's `schema.properties`.

### ❌ Using `type` on a body parameter
```yaml
parameters:
  - name: body
    in: body
    type: object    # ❌ — use schema, not type, for body params
    schema:
      type: object  # ✅
```

### ❌ Forgetting quotes around special YAML characters
```yaml
description: This endpoint returns user: data  # Colon mid-string can break parsing
description: "This endpoint returns user: data" # ✅
```

### ❌ Wrong `in` value for path parameters
If your route is `/users/<user_id>`, that parameter must be `in: path` and `required: true` — not `in: query`.

---

## 5. Complete Working Example — POST Endpoint

This is a fully valid Flasgger docstring for a `POST /tracks/upload` endpoint that accepts both a query parameter and a JSON body.

```python
from flask import Flask, request, jsonify
from flasgger import Swagger

app = Flask(__name__)
swagger = Swagger(app)

@app.route("/tracks/upload", methods=["POST"])
def upload_track():
    """
    Upload a new track to the catalog.
    Accepts track metadata as JSON and an optional source label as a query param.
    ---
    tags:
      - Tracks
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: source
        in: query
        type: string
        required: false
        description: Origin label or distribution source (e.g. 'distrokid', 'direct').
        default: direct
        enum:
          - distrokid
          - tunecore
          - direct
      - name: body
        in: body
        required: true
        description: Track metadata payload.
        schema:
          type: object
          required:
            - title
            - artist
          properties:
            title:
              type: string
              description: Track title.
              example: Neon Frequency
            artist:
              type: string
              description: Primary artist name.
              example: Brett & The Signal
            isrc:
              type: string
              description: International Standard Recording Code.
              example: USRC12345678
            duration_seconds:
              type: integer
              description: Track length in seconds.
              example: 214
            explicit:
              type: boolean
              description: Whether the track contains explicit content.
              default: false
            genre:
              type: string
              description: Primary genre classification.
              example: Electronic
    responses:
      201:
        description: Track successfully uploaded and queued for processing.
        schema:
          type: object
          properties:
            track_id:
              type: string
              example: trk_9f3a12bc
            status:
              type: string
              example: queued
            message:
              type: string
              example: Track received and queued for processing.
      400:
        description: Validation error — missing required fields or malformed JSON.
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Field 'artist' is required."
      422:
        description: Unprocessable entity — ISRC format invalid or duplicate detected.
      500:
        description: Internal server error.
    """
    data = request.get_json()
    source = request.args.get("source", "direct")
    # ... your handler logic ...
    return jsonify({"track_id": "trk_9f3a12bc", "status": "queued"}), 201
```

---

## 6. Flasgger-Specific Quirks and Recommendations

### Swagger version
Flasgger defaults to **Swagger 2.0** (not OpenAPI 3.x). The `in: body` pattern, `type` on parameters, and `$ref` syntax all follow 2.0 conventions. Don't mix in OpenAPI 3.0 constructs (`requestBody`, `components/schemas`) unless you've explicitly configured Flasgger for 3.x.

### YAML lives in the Python indent context
Flasgger parses the docstring with `yaml.safe_load` after stripping the common leading whitespace. This means your YAML indentation is **relative to itself**, not the Python function body — but it must be internally consistent.

### `$ref` for reusable schemas
You can define shared schemas in the Flasgger config's `template` and reference them:
```yaml
schema:
  $ref: '#/definitions/Track'
```
Define `Track` under `swagger_config["template"]["definitions"]` in your app setup.

### Swagger UI `example` vs `examples`
Inside `schema.properties`, use `example` (singular, Swagger 2.0). The plural `examples` belongs to the response level and has limited UI support in Flasgger.

### `operationId` uniqueness
If you use `operationId`, it must be unique across the entire spec. Flasgger will silently accept duplicates but generated clients will break.

### Validation on startup
Add `Swagger(app, parse=True)` to validate all docstrings at startup and catch YAML errors early — especially useful during development.

### Boolean and null values
Use unquoted `true`/`false`/`null` — these are native YAML types. Quoting them (`"true"`) turns them into strings, which will fail Swagger validation on boolean fields.

```yaml
required: true      # ✅ boolean
required: "true"    # ❌ string — will cause a spec validation warning
```

---

*Swagger 2.0 spec reference: https://swagger.io/specification/v2/*
*Flasgger docs: https://github.com/flasgger/flasgger*
