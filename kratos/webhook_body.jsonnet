function(ctx) {
  identity_id: ctx.identity.id,
  email: ctx.identity.traits.email,
  first_name: ctx.identity.traits.first_name,
  last_name: ctx.identity.traits.last_name,
  mobile: ctx.identity.traits.mobile,
  role: if std.objectHas(ctx.identity.traits, "role") then ctx.identity.traits.role else "inspector"
}