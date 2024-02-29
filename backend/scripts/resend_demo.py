import resend

resend.api_key = "re_2qSfJ45g_LTw7wirBUAZyZBJBci9GenER"

r = resend.Emails.send(
    {
        "from": "onboarding@resend.dev",
        "to": "plb@phospho.app",
        "subject": "Hello World",
        "html": "<p>Congrats on sending your <strong>first email</strong>!</p>",
    }
)
