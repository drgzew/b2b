import React from "react";
import CuratorLayout from "../layouts/CuratorLayout";
import PartnerLayout from "../layouts/PartnerLayout";

interface RoleLayoutProps {
    children: React.ReactNode;
}

export default function RoleLayout({
    children
}: RoleLayoutProps) {

    const role = localStorage.getItem("role");

    if (role === "curator") {
        return (
            <CuratorLayout>
                {children}
            </CuratorLayout>
        );
    }

    if (role === "partner") {
        return (
            <PartnerLayout>
                {children}
            </PartnerLayout>
        );
    }

    return (
        <>
            {children}
        </>
    );
}