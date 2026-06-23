"""Konkretne widoki aplikacji. Wszystkie dziedzicza z ListView (front.views.base)."""

from front.views.base import View, ListView
from front.views.nawyki import NawykiView
from front.views.wszystkie import WszystkieView
from front.views.dzis import DzisView

__all__ = ["View", "ListView", "NawykiView", "WszystkieView", "DzisView"]