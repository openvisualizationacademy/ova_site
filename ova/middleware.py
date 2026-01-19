class AzureProxyMiddleware:
    """Fix X-Forwarded-For header from Azure proxy (strips port from IP)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ips = x_forwarded_for.split(",")
            first_ip = ips[0].strip()

            # Strip port if present (Azure includes it)
            if ":" in first_ip and not first_ip.startswith("["):
                first_ip = first_ip.rsplit(":", 1)[0]

            ips[0] = first_ip
            request.META["HTTP_X_FORWARDED_FOR"] = ",".join(ips)

        return self.get_response(request)
