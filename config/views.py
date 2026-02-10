from django.http import JsonResponse, HttpResponse


def home(request):
    # Configuration variables
    project_name = "Django REST API"  # Your dynamic project name
    # Set your GitHub username
    github_repo_url = "#"
    # Set your Postman collection URL
    postman_docs_url = "#"
    description = "This is a Django REST API stater template. You can use this template as a starting point for your own Django REST API project."
    show_admin_credentials = False  # Set to True to show admin credentials button

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{project_name} - REST API</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}

                body {{
                    background: #f8f9fa;
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    color: #2c3e50;
                }}

                .container {{
                    background: white;
                    border-radius: 12px;
                    padding: 50px 40px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                    text-align: center;
                    max-width: 500px;
                    width: 90%;
                    border: 1px solid #e9ecef;
                }}

                .spinner {{
                    width: 40px;
                    height: 40px;
                    border: 3px solid #e9ecef;
                    border-top: 3px solid #28a745;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin: 0 auto 30px auto;
                }}

                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}

                h1 {{
                    font-size: 2.5rem;
                    font-weight: 300;
                    margin-bottom: 8px;
                    color: #2c3e50;
                }}

                .project-name {{
                    color: #28a745;
                    font-weight: 500;
                }}

                .subtitle {{
                    color: #6c757d;
                    font-size: 1.1rem;
                    margin-bottom: 40px;
                    font-weight: 400;
                }}

                .status {{
                    display: inline-flex;
                    align-items: center;
                    background: #d4edda;
                    color: #155724;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                    margin-bottom: 30px;
                    border: 1px solid #c3e6cb;
                }}

                .status-dot {{
                    width: 6px;
                    height: 6px;
                    background: #28a745;
                    border-radius: 50%;
                    margin-right: 8px;
                }}

                .button-grid {{
                    display: grid;
                    gap: 15px;
                    margin-top: 30px;
                }}

                .btn {{
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 14px 20px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 500;
                    font-size: 15px;
                    transition: all 0.2s ease;
                    border: 1px solid transparent;
                }}

                .btn-admin {{
                    background: #007bff;
                    color: white;
                    border-color: #007bff;
                }}

                .btn-admin:hover {{
                    background: #0056b3;
                    transform: translateY(-1px);
                }}

                .btn-repo {{
                    background: #24292e;
                    color: white;
                    border-color: #24292e;
                }}

                .btn-repo:hover {{
                    background: #1e2125;
                    transform: translateY(-1px);
                }}

                .btn-postman {{
                    background: #ff6c37;
                    color: white;
                    border-color: #ff6c37;
                }}

                .btn-postman:hover {{
                    background: #e85d2c;
                    transform: translateY(-1px);
                }}

                .btn-credentials {{
                    background: white;
                    color: #28a745;
                    border-color: #28a745;
                }}

                .btn-credentials:hover {{
                    background: #28a745;
                    color: white;
                    transform: translateY(-1px);
                }}

                .btn-icon {{
                    margin-right: 8px;
                }}

                .footer {{
                    margin-top: 35px;
                    padding-top: 25px;
                    border-top: 1px solid #e9ecef;
                    color: #6c757d;
                    font-size: 13px;
                }}

                @media (max-width: 600px) {{
                    .container {{
                        padding: 40px 25px;
                    }}
                    h1 {{
                        font-size: 2rem;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="spinner"></div>
                
                <h1>Welcome to <span class="project-name">{project_name}</span></h1>
                <p class="subtitle">REST API Server</p>

                
                <div class="status">
                    <div class="status-dot"></div>
                    Server Running
                </div>

                <div class="button-grid">
                    <a href="/admin/custom_home/dashboarddummy/" class="btn btn-admin">
                        <span class="btn-icon">⚙️</span>
                        Admin Dashboard
                    </a>
                    
                    <a href="{github_repo_url}" class="btn btn-repo" target="_blank">
                        <span class="btn-icon">📁</span>
                        View Repository
                    </a>
                    
                    <a href="{postman_docs_url}" class="btn btn-postman" target="_blank">
                        <span class="btn-icon">📋</span>
                        API Docs (Postman)
                    </a>
                    
                    {"<a href='/admin-credentials/' class='btn btn-credentials'><span class='btn-icon'>🔑</span>Admin Credentials</a>" if show_admin_credentials else ""}
                </div>
                
              
                
                <div class="footer">
                <div class ="description">
                    <p>{description}</p>
                    <br>
                </div>
                    <p>Built with Django Framework</p>
                </div>
            </div>
        </body>
    </html>
    """
    return HttpResponse(html_content)
