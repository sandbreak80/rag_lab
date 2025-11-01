import React from 'react';
import { Outlet } from 'react-router-dom';
import { Header } from './Header';
import { TabNavigation } from './TabNavigation';

export function AppLayout() {
  return (
    <div className="flex flex-col min-h-screen bg-background">
      <Header />
      <TabNavigation />
      <main className="flex-1 container mx-auto px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}

