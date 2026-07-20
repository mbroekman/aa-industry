"""Hook into Alliance Auth"""

# Django
from django.utils.translation import gettext_lazy as _

# Alliance Auth
from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

# AA Industry App
from industry_reforged import urls


class PersonalIndustryMenuItem(MenuItemHook):
    """This class ensures only authorized users will see the menu entry"""

    def __init__(self):
        # setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            _("Personal Industry"),
            "fas fa-cube fa-fw",
            "industry_reforged:personal_dashboard",
            navactive=[
                "industry_reforged:personal_dashboard",
                "industry_reforged:index",
            ],
        )

    def render(self, request):
        if request.user.has_perm("industry_reforged.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


class CorporateIndustryMenuItem(MenuItemHook):
    """Menu entry for Corporate Industry"""

    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("Corporate Industry"),
            "fas fa-building fa-fw",
            "industry_reforged:corporate_dashboard",
            navactive=["industry_reforged:corporate_dashboard"],
        )

    def render(self, request):
        if request.user.has_perm("industry_reforged.corp_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_personal_menu():
    """Register the personal menu item"""
    return PersonalIndustryMenuItem()


@hooks.register("menu_item_hook")
def register_corporate_menu():
    """Register the corporate menu item"""
    return CorporateIndustryMenuItem()


class MemberOrdersMenuItem(MenuItemHook):
    """Menu entry for Member Orders (Self Service)"""

    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("Member Orders"),
            "fas fa-shopping-cart fa-fw",
            "industry_reforged:orders_dashboard",
            navactive=[
                "industry_reforged:orders_dashboard",
                "industry_reforged:create_order",
            ],
        )

    def render(self, request):
        if request.user.has_perm("industry_reforged.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_member_orders_menu():
    """Register the member orders menu item"""
    return MemberOrdersMenuItem()


class IndustrialistMenuItem(MenuItemHook):
    """Menu entry for Industrialist Dashboard"""

    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("Industrialist Dash"),
            "fas fa-hammer fa-fw",
            "industry_reforged:industrialist_dashboard",
            navactive=[
                "industry_reforged:industrialist_dashboard",
            ],
        )

    def render(self, request):
        if request.user.has_perm("industry_reforged.industrialist_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_industrialist_menu():
    """Register the industrialist menu item"""
    return IndustrialistMenuItem()


class DirectorMenuItem(MenuItemHook):
    """Menu entry for Director Control Panel"""

    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("Director CP"),
            "fas fa-chess-king fa-fw",
            "industry_reforged:director_dashboard",
            navactive=[
                "industry_reforged:director_dashboard",
                "industry_reforged:director_inventory",
                "industry_reforged:director_config",
            ],
        )

    def render(self, request):
        if request.user.has_perm("industry_reforged.corp_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_director_menu():
    """Register the director menu item"""
    return DirectorMenuItem()


class LeaderboardMenuItem(MenuItemHook):
    """Menu entry for Leaderboard (Viewable by everyone)"""

    def __init__(self):
        MenuItemHook.__init__(
            self,
            _("Industry Leaderboard"),
            "fas fa-trophy fa-fw",
            "industry_reforged:industrialist_leaderboard",
            navactive=["industry_reforged:industrialist_leaderboard"],
        )

    def render(self, request):
        if request.user.has_perm("industry_reforged.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_leaderboard_menu():
    """Register the leaderboard menu item"""
    return LeaderboardMenuItem()


@hooks.register("url_hook")
def register_urls():
    """Register app urls"""

    return UrlHook(urls, "industry_reforged", r"^industry/")
