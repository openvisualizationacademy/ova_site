from allauth.account.adapter import DefaultAccountAdapter


AUTH_SENDER = "donotreply@openvisualizationacademy.org"


class ACSAccountAdapter(DefaultAccountAdapter):
    """
    Enforces a valid ACS Email REST sender for all auth emails.
    """

    def send_mail(self, template_prefix, email, context):
        msg = self.render_mail(template_prefix, email, context)

        # HARD OVERRIDE sender (critical for ACS REST)
        msg.from_email = AUTH_SENDER

        msg.send()
