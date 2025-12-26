import React from "react";
import { TopNav } from "./TopNav";

type AppShellProps = {
  children: React.ReactNode;
};

export const AppShell = ({ children }: AppShellProps) => {
  return (
    <div className="AppFrame">
      <TopNav />
      <header className="mb-6 mt-20 max-w-2xl mx-auto">
        <h1 className="Headline text-3xl text-Ink md:text-4xl">
          Portion Note
        </h1>
      </header>
      <main className="flex-1 space-y-6 pb-6">{children}</main>
    </div>
  );
};
