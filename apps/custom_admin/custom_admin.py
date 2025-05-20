from django.utils.translation import gettext_lazy as _
from django.templatetags.static import static



UNFOLD = {
    "DASHBOARD_TEMPLATE": "dashboard.html",
    "SITE_TITLE": "Admin Dashboard",
    "SITE_HEADER": "Administration",
    "SITE_URL": "https://puttputtplay.com/",
    "SITE_SYMBOL": "admin_panel_settings",
    "LOGO": lambda request: static("images/logo.png"),
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_SITE_HEADER": True,
    
    "FORMS": {
    "INLINE_ACTIONS": True,
},
      "SITE_ICON": {
        "light": lambda request: static("https://nyc3.digitaloceanspaces.com/smtech-space/uploads/yaribabi_1761965858_5080.png"),  # light mode
        "dark": lambda request: static("https://nyc3.digitaloceanspaces.com/smtech-space/uploads/yaribabi_1761965858_5080.png"),  # dark mode
    },
    # "SITE_LOGO": lambda request: static("logo.svg"),  # both modes, optimise for 32px height
    "SITE_LOGO": {
        "light": lambda request: static("https://nyc3.digitaloceanspaces.com/smtech-space/uploads/yaribabi_1761965858_5080.png"),  # light mode
        "dark": lambda request: static("https://nyc3.digitaloceanspaces.com/smtech-space/uploads/yaribabi_1761965858_5080.png"),  # dark mode
    },
   
    "THEME": "light",
    "ACTIONS": {
        "ENABLE_DELETE": True,
        "ENABLE_ADD": True,
        "ENABLE_CHANGE": True,
        "ENABLE_BULK_DELETE": True,
    },

    "ENVIRONMENT": "Development",

    "LOGIN": {
        "redirect_after": lambda request: "/admin/",
    },
    "STYLES": [
        lambda request: static("css/custom_admin.css"),
    ],
    "SCRIPTS": [
        lambda request: static("js/custom_admin.js"),
    ],
    
   "BORDER_RADIUS": "6px",
    "COLORS": {
        "base": {
            "50": "oklch(98.5% .002 247.839)",
            "100": "oklch(96.7% .003 264.542)",
            "200": "oklch(92.8% .006 264.531)",
            "300": "oklch(87.2% .01 258.338)",
            "400": "oklch(70.7% .022 261.325)",
            "500": "oklch(55.1% .027 264.364)",
            "600": "oklch(44.6% .03 256.802)",
            "700": "oklch(37.3% .034 259.733)",
            "800": "oklch(27.8% .033 256.848)",
            "900": "oklch(21% .034 264.665)",
            "950": "oklch(13% .028 261.692)",
        },

        # ✅ Custom primary palette (green #0D9125 based)
        "primary": {
            "50": "oklch(97% .03 145)",   # very light tint
            "100": "oklch(93% .05 145)",
            "200": "oklch(87% .08 145)",
            "300": "oklch(80% .12 145)",
            "400": "oklch(70% .16 145)",
            "500": "oklch(60% .18 145)",  # main #0D9125 base tone
            "600": "oklch(52% .18 145)",
            "700": "oklch(45% .16 145)",
            "800": "oklch(38% .13 145)",
            "900": "oklch(31% .10 145)",
            "950": "oklch(22% .08 145)",
        },

        "font": {
            "subtle-light": "var(--color-base-500)",  # text-base-500
            "subtle-dark": "var(--color-base-400)",  # text-base-400
            "default-light": "var(--color-base-600)",  # text-base-600
            "default-dark": "var(--color-base-300)",  # text-base-300
            "important-light": "var(--color-base-900)",  # text-base-900
            "important-dark": "var(--color-base-100)",  # text-base-100
        },
    },

    "EXTENSIONS": {
        "modeltranslation": {
            "flags": {"en": "🇺🇸", "bn": "🇧🇩"},
        },
    },

    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
        {
                
                "icon": "dashboard",
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": "Dashboard ",
                        "icon": "dashboard",
                        "link": "/admin/custom_home/dashboarddummy/",
                    }
                ],
            },
        
            
            {
                "title": _("User Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {"title": _("Admins"), "icon": "verified_user", "link": "/admin/auths/customuser/admins/"},
                    {"title": _("Staff Members"), "icon": "supervisor_account", "link": "/admin/auths/customuser/staff/"},
                    {"title": _("Regular Users"), "icon": "person", "link": "/admin/auths/customuser/users/"},
                    {"title": _("Groups"), "icon": "group", "link": "/admin/auth/group/"},
                    {"title": _("Contact Messages"), "icon": "contact_mail", "link": "/admin/auths/contactmessage/"},
                    {"title": _("Help Us Improve"), "icon": "feedback", "link": "/admin/auths/helpusimprove/"},
                ],
            },

            {
                "title": _("Notifications"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {"title": _("All Notifications"), "icon": "notifications", "link": "/admin/notification/notification/"},
                ],
            },
        ],
    },

    "TABS": [
        {
            "models": ["auths.customuser"],
            "items": [
                {"title": _("All Users"), "link": "/admin/auths/customuser/"},
                {"title": _("Active"), "link": "/admin/auths/customuser/?is_active__exact=1"},
                {"title": _("Verified"), "link": "/admin/auths/customuser/?is_verified__exact=1"},
            ],
        },
    ],
}
