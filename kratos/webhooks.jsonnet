function(ctx) {
  // This webhook is called after successful registration
  // It syncs Kratos identities with the application's user database
  
  if (ctx.flow.type == "registration" && ctx.flow.state == "passed_challenge") {
    {
      method: "POST",
      url: "http://backend:8000/auth/kratos/webhook",
      body: {
        identity_id: ctx.identity.id,
        email: ctx.identity.traits.email,
        first_name: ctx.identity.traits.first_name,
        last_name: ctx.identity.traits.last_name,
        mobile: ctx.identity.traits.mobile,
        role: ctx.identity.traits.role
      },
      headers: {
        "Content-Type": "application/json",
        "X-Kratos-Webhook-Token": std.extVar("KRATOS_WEBHOOK_SECRET")
      }
    }
  }
}