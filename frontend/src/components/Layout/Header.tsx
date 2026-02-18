import { useContext } from 'react';
import { LogOut, Sun, Moon, Settings } from 'lucide-react';
import logo from '@/assets/logo.png';
import { useNavigate, useLocation } from '@tanstack/react-router';
import { useUnifiedAuth } from '../../hooks/useUnifiedAuth';
import { ColorModeContext } from '../../ColorModeContext';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

const adminNav = [
  { label: 'Orders', path: '/orders' },
  { label: 'Scan', path: '/stock/scan' },
  { label: 'Labels', path: '/stock/labels' },
  { label: 'Stock', path: '/stock' },
  { label: 'Tasks', path: '/stock/verification' },
  { label: 'Products', path: '/products' },
  { label: 'Raw Materials', path: '/raw-materials' },
  { label: 'Reports', path: '/reports' },
];

const warehouseNav = [
  { label: 'Scan', path: '/stock/scan' },
  { label: 'Labels', path: '/stock/labels' },
  { label: 'Stock', path: '/stock' },
  { label: 'Tasks', path: '/stock/verification' },
];

function getNavItems(role?: string) {
  if (role === 'warehouse') return warehouseNav;
  return adminNav;
}

export function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useUnifiedAuth();
  const colorMode = useContext(ColorModeContext);

  const handleLogout = async () => {
    await logout();
    navigate({ to: '/login' });
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-gray-100 dark:border-gray-800 bg-white/95 dark:bg-gray-950/95 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-gray-950/60">
      <div className="flex h-20 items-center px-4">
        {/* Left side - Logo */}
        <button
          onClick={() => navigate({ to: '/dashboard' })}
          className="flex items-center cursor-pointer bg-transparent border-none p-0"
        >
          <img
            src={logo}
            alt="Ramjet Plastics"
            className="h-16 w-auto brightness-[1.15] mix-blend-multiply dark:invert dark:brightness-100 dark:mix-blend-screen"
          />
        </button>

        {/* Navigation */}
        <nav className="ml-8 flex items-center gap-1">
          {getNavItems(user?.role).map((item) => (
            <button
              key={item.path}
              onClick={() => navigate({ to: item.path })}
              className={`relative px-3 py-1.5 text-sm font-semibold uppercase tracking-wide transition-colors rounded-md ${
                location.pathname.startsWith(item.path)
                  ? 'text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {item.label}
              {location.pathname.startsWith(item.path) && (
                <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-foreground rounded-full" />
              )}
            </button>
          ))}
        </nav>

        {/* Right side - User, Theme, Logout */}
        <div className="ml-auto flex items-center gap-2">
          {/* User Dropdown */}
          {user && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="relative h-14 w-14 rounded-full p-0">
                  <Avatar className="h-14 w-14">
                    <AvatarFallback className="text-xl font-semibold">
                      {user.first_name?.[0]?.toUpperCase()}{user.last_name?.[0]?.toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {user.first_name} {user.last_name}
                    </p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {user.email}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate({ to: '/settings' })}>
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}

          {/* Theme Toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={colorMode.toggleColorMode}
            className="relative h-14 w-14"
          >
            <Sun className="h-7 w-7 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-7 w-7 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
            <span className="sr-only">Toggle theme (currently {colorMode.mode})</span>
          </Button>

          {/* Logout Button (visible on mobile) */}
          <Button
            variant="ghost"
            size="icon"
            onClick={handleLogout}
            className="h-9 w-9 sm:hidden"
          >
            <LogOut className="h-4 w-4" />
            <span className="sr-only">Logout</span>
          </Button>
        </div>
      </div>
    </header>
  );
}