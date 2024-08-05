import resend

resend.api_key = "re_randomcharacters"

r = resend.Emails.send(
    {
        "from": "onboarding@resend.dev",
        "to": "target.email@company.com",
        "subject": "Hello World",
        "html": "<p>Congrats on sending your <strong>first email</strong>!</p>",
    }
)
