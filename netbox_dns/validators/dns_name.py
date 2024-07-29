import re

from django.core.exceptions import ValidationError

from netbox.plugins.utils import get_plugin_config


__all__ = (
    "validate_fqdn",
    "validate_generic_name",
    "validate_domain_name",
)


def _get_label(tolerate_leading_underscores=False, always_tolerant=False):
    tolerate_characters = re.escape(
        get_plugin_config("netbox_dns", "tolerate_characters_in_zone_labels", "")
    )
    label_characters = rf"a-z0-9{tolerate_characters}"

    if always_tolerant:
        label = r"[a-z0-9_][a-z0-9_-]*(?<![-_])"
        zone_label = rf"[{label_characters}_][{label_characters}_-]*(?<![-_])"

        return label, zone_label

    tolerate_underscores = get_plugin_config(
        "netbox_dns", "tolerate_underscores_in_labels"
    ) or get_plugin_config("netbox_dns", "tolerate_underscores_in_hostnames")

    if tolerate_leading_underscores:
        if tolerate_underscores:
            label = r"[a-z0-9_][a-z0-9_-]*(?<![-_])"
            zone_label = rf"[{label_characters}_][{label_characters}_-]*(?<![-_])"
        else:
            label = r"[a-z0-9_][a-z0-9-]*(?<!-)"
            zone_label = rf"[{label_characters}_][{label_characters}-]*(?<!-)"
    elif tolerate_underscores:
        label = r"[a-z0-9][a-z0-9_-]*(?<![-_])"
        zone_label = rf"[{label_characters}][{label_characters}_-]*(?<![-_])"
    else:
        label = r"[a-z0-9][a-z0-9-]*(?<!-)"
        zone_label = rf"[{label_characters}][{label_characters}-]*(?<!-)"

    return label, zone_label


def _has_invalid_double_dash(name):
    return bool(re.findall(r"\b(?!xn)..--", name, re.IGNORECASE))


def validate_fqdn(name, always_tolerant=False):
    label, zone_label = _get_label(always_tolerant=always_tolerant)
    regex = rf"^(\*|{label})(\.{zone_label})+\.?$"

    if not re.match(regex, name, flags=re.IGNORECASE) or _has_invalid_double_dash(name):
        raise ValidationError(f"{name} is not a valid fully qualified DNS host name")


def validate_generic_name(
    name, tolerate_leading_underscores=False, always_tolerant=False
):
    label, zone_label = _get_label(
        tolerate_leading_underscores=tolerate_leading_underscores,
        always_tolerant=always_tolerant,
    )
    regex = rf"^([*@]|(\*\.)?{label}(\.{zone_label})*\.?)$"

    if not re.match(regex, name, flags=re.IGNORECASE) or _has_invalid_double_dash(name):
        raise ValidationError(f"{name} is not a valid DNS host name")


def validate_domain_name(
    name, always_tolerant=False, allow_empty_label=False, zone_name=False
):
    if name == "@" and allow_empty_label:
        return

    if name == "." and (
        always_tolerant or get_plugin_config("netbox_dns", "enable_root_zones")
    ):
        return

    label, zone_label = _get_label(always_tolerant=always_tolerant)
    if zone_name:
        regex = rf"^{zone_label}(\.{zone_label})*\.?$"
    else:
        regex = rf"^{label}(\.{zone_label})*\.?$"

    if not re.match(regex, name, flags=re.IGNORECASE) or _has_invalid_double_dash(name):
        raise ValidationError(f"{name} is not a valid DNS domain name")
