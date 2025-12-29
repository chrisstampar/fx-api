"""
Middleware to inject custom CSS into Swagger UI for better readability.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse
import re


class SwaggerCSSMiddleware(BaseHTTPMiddleware):
    """Inject custom CSS into Swagger UI HTML."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only modify Swagger UI HTML responses
        if request.url.path == "/docs" and response.status_code == 200:
            # Get response body
            if hasattr(response, "body"):
                try:
                    body = response.body.decode("utf-8") if isinstance(response.body, bytes) else str(response.body)
                except:
                    return response
                
                # Inject custom CSS before closing head tag
                css_injection = """
                <style>
                /* Custom Swagger UI Styles for Better Readability */
                .swagger-ui .info .title { color: #1f2937 !important; font-size: 36px !important; font-weight: 700 !important; }
                .swagger-ui .info .description { color: #374151 !important; font-size: 14px !important; line-height: 1.6 !important; }
                .swagger-ui .opblock-body pre { background-color: #f7f7f7 !important; border: 1px solid #e0e0e0 !important; color: #1f2937 !important; font-size: 13px !important; line-height: 1.6 !important; }
                .swagger-ui .opblock-body pre code { color: #1f2937 !important; background: transparent !important; }
                .swagger-ui .parameter__name { color: #1f2937 !important; font-weight: 600 !important; }
                .swagger-ui .parameter__type { color: #3b82f6 !important; font-weight: 500 !important; }
                .swagger-ui .parameter__description { color: #4b5563 !important; line-height: 1.6 !important; }
                .swagger-ui table thead tr th { background-color: #f9fafb !important; color: #1f2937 !important; font-weight: 600 !important; }
                .swagger-ui table tbody tr td { color: #374151 !important; border-color: #e5e7eb !important; }
                .swagger-ui .response-col_status { font-weight: 600 !important; }
                .swagger-ui .btn.execute { background-color: #3b82f6 !important; color: white !important; font-weight: 600 !important; }
                .swagger-ui .btn.execute:hover { background-color: #2563eb !important; }
                .swagger-ui .model-box { background-color: #f9fafb !important; border: 1px solid #e5e7eb !important; }
                .swagger-ui .model-title { color: #1f2937 !important; font-weight: 600 !important; }
                .swagger-ui .property-name { color: #1f2937 !important; font-weight: 600 !important; }
                .swagger-ui .property-type { color: #3b82f6 !important; }
                .swagger-ui { color: #374151 !important; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important; }
                .swagger-ui p { color: #4b5563 !important; line-height: 1.6 !important; }
                .swagger-ui .parameter__required { color: #dc2626 !important; font-weight: 600 !important; }
                .swagger-ui input[type="text"], .swagger-ui input[type="password"], .swagger-ui textarea { border: 1px solid #d1d5db !important; color: #1f2937 !important; background-color: white !important; }
                .swagger-ui input[type="text"]:focus, .swagger-ui input[type="password"]:focus, .swagger-ui textarea:focus { border-color: #3b82f6 !important; outline: 2px solid rgba(59, 130, 246, 0.2) !important; }
                </style>
                """
                
                # Inject CSS before </head> or before </body>
                if "</head>" in body:
                    body = body.replace("</head>", css_injection + "</head>")
                    return HTMLResponse(content=body, status_code=response.status_code)
                elif "<body>" in body and "</head>" not in body:
                    # If no head tag, inject at start of body
                    body = body.replace("<body>", "<head>" + css_injection + "</head><body>")
                    return HTMLResponse(content=body, status_code=response.status_code)
        
        return response

