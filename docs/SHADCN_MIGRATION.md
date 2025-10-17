# shadcn/ui Migration Summary

## Overview
This document summarizes the migration from Material-UI (MUI) to shadcn/ui components completed on 2025-08-08.

## Migration Scope

### What Changed
1. **UI Framework**: MUI → shadcn/ui + Tailwind CSS
2. **Styling**: CSS-in-JS (emotion) → Tailwind utility classes
3. **Component Library**: MUI components → shadcn/ui components
4. **Theme System**: MUI theme → CSS variables + Tailwind config
5. **Dark Mode**: MUI theme → Tailwind `dark` class

### Migration Statistics
- **Components migrated**: ~20 files
- **shadcn components added**: 16 (button, card, input, label, form, checkbox, alert, separator, tabs, skeleton, textarea, select, switch, dialog, sheet, tooltip)
- **Dependencies removed**: @mui/material, @emotion/react, @emotion/styled (pending)
- **Dependencies added**: class-variance-authority, clsx, tailwind-merge

## Technical Details

### shadcn/ui Setup
1. **Import alias configured**: `@/` → `./src/`
2. **Components location**: `src/components/ui/`
3. **Utilities**: `src/lib/utils.ts` with `cn()` helper
4. **Configuration**: `components.json` for shadcn CLI

### Tailwind Configuration
- **Version**: Tailwind CSS v4
- **Config**: Extended with shadcn color tokens and radius variables
- **CSS Variables**: Comprehensive theming system in `src/index.css`
- **Dark Mode**: Class-based dark mode with `dark` class on root

### Component Mapping
| MUI Component | shadcn/ui Replacement |
|--------------|----------------------|
| Box | `div` with Tailwind classes |
| Typography | Semantic HTML (`h1`, `p`) with classes |
| Button | `Button` component |
| TextField | `Input` + `Label` components |
| Paper | `Card` component |
| Tabs | `Tabs`, `TabsList`, `TabsTrigger`, `TabsContent` |
| Alert | `Alert` component |
| Checkbox | `Checkbox` component |
| CircularProgress | Custom spinner with Tailwind animation |

## Key Files Updated

### Core Components
1. **KratosFlow.tsx**: Complete rewrite using shadcn form components
2. **Settings page**: Replaced MUI Tabs with shadcn Tabs
3. **Layout components**: Converted to Tailwind classes
4. **Auth pages**: Already using Tailwind (no changes needed)

### Configuration Files
1. **tsconfig.json**: Added path alias for `@/`
2. **vite.config.ts**: Added resolve alias
3. **tailwind.config.js**: Extended with shadcn tokens
4. **package.json**: Updated dependencies

## Migration Process

### Step 1: Initialize shadcn/ui
```bash
npx shadcn@latest init
```
- Fixed "use client" directives (Next.js specific)
- Configured TypeScript paths
- Set up Tailwind integration

### Step 2: Generate Components
```bash
npx shadcn@latest add button card input label form checkbox alert separator tabs skeleton
npx shadcn@latest add textarea select switch dialog sheet tooltip
```

### Step 3: Update Components
1. Settings page: MUI Tabs → shadcn Tabs
2. KratosFlow: MUI form elements → shadcn form components
3. Fixed React imports where needed
4. Removed "use client" directives from Vite app

### Step 4: Fix Issues
- Installed missing `class-variance-authority` dependency
- Removed "use client" directives causing crashes
- Updated imports to use `@/` alias

## Benefits of Migration

1. **Performance**: Smaller bundle size without MUI
2. **Customization**: Full control over component styling
3. **Modern Stack**: Latest UI patterns and practices
4. **Type Safety**: Better TypeScript integration
5. **Consistency**: Unified styling approach with Tailwind

## Remaining Tasks

### High Priority
- [ ] Remove MUI dependencies from package.json
- [ ] Update simple-login.tsx and simple-register.tsx (if still needed)

### Low Priority
- [ ] Optimize Tailwind production build
- [ ] Add custom animations
- [ ] Create reusable compound components

## Common Patterns

### Form Fields
```tsx
<div className="space-y-2">
  <Label htmlFor="email">Email</Label>
  <Input id="email" type="email" />
</div>
```

### Cards
```tsx
<Card>
  <CardHeader>
    <CardTitle>Title</CardTitle>
  </CardHeader>
  <CardContent>
    Content here
  </CardContent>
</Card>
```

### Buttons
```tsx
<Button variant="default">Primary</Button>
<Button variant="outline">Secondary</Button>
<Button variant="destructive">Danger</Button>
```

### Spinners
```tsx
<div className="animate-spin rounded-full h-6 w-6 border-2 border-muted-foreground border-t-transparent" />
```

## Troubleshooting

### Issue: "use client" errors
**Solution**: Remove these directives - they're Next.js specific

### Issue: Missing styles
**Solution**: Ensure Tailwind content paths include all component files

### Issue: Dark mode not working
**Solution**: Check that `dark` class is toggled on document root

### Issue: Component not found
**Solution**: Run `npx shadcn@latest add <component>` to generate it

---
*Migration completed successfully with all core functionality preserved*