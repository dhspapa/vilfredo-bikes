from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Reservation


class ReservationForm(forms.ModelForm):
    accept_terms = forms.BooleanField(
        required=True,
        label=_(
            "I accept the rental terms and responsibility notice. I confirm that I am "
            "responsible for safe use, delays, damage, loss, theft, traffic violations, "
            "and accidents during the rental period."
        ),
        widget=forms.CheckboxInput(
            attrs={"class": "form-check-input terms-checkbox"}
        ),
        error_messages={"required": _("You must accept the rental terms to continue.")},
    )

    class Meta:
        model = Reservation
        fields = [
            "full_name",
            "email",
            "phone",
            "booking_reference",
            "property_name",
            "check_in",
            "check_out",
            "rental_start",
            "rental_end",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "booking_reference": forms.TextInput(attrs={"class": "form-control"}),
            "property_name": forms.Select(attrs={"class": "form-select"}),
            "check_in": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "check_out": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "rental_start": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "rental_end": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def __init__(self, *args, property_name=None, **kwargs):
        self.fixed_property_name = property_name
        super().__init__(*args, **kwargs)
        self.fields["full_name"].label = _("Full name")
        self.fields["email"].label = _("Email")
        self.fields["phone"].label = _("Phone")
        self.fields["booking_reference"].label = _("Booking reference")
        self.fields["property_name"].label = _("Property")
        self.fields["check_in"].label = _("Check-in date")
        self.fields["check_out"].label = _("Check-out date")
        self.fields["rental_start"].label = _("Rental start date")
        self.fields["rental_end"].label = _("Rental end date")

        if property_name:
            self.fields["property_name"].initial = property_name
            self.fields["property_name"].widget = forms.HiddenInput()

        required_message = _("This field is required.")
        for field_name in (
            "full_name",
            "email",
            "phone",
            "booking_reference",
            "check_in",
            "check_out",
            "rental_start",
            "rental_end",
        ):
            self.fields[field_name].error_messages["required"] = required_message
        self.fields["email"].error_messages["invalid"] = _("Enter a valid email address.")

    def clean_property_name(self):
        if self.fixed_property_name:
            return self.fixed_property_name
        return self.cleaned_data.get("property_name")

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get("check_in")
        check_out = cleaned.get("check_out")
        rental_start = cleaned.get("rental_start")
        rental_end = cleaned.get("rental_end")

        if check_in and check_out and check_in > check_out:
            raise forms.ValidationError(_("Check-out must be on or after check-in."))

        if rental_start and rental_end and rental_end < rental_start:
            raise forms.ValidationError(_("Rental end must be on or after rental start."))

        if check_in and rental_start and rental_start < check_in:
            raise forms.ValidationError(_("Rental start must be on or after check-in."))

        if check_out and rental_end and rental_end > check_out:
            raise forms.ValidationError(_("Rental end must be on or before check-out."))

        return cleaned
