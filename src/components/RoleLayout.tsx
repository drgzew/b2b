import React from "react";
import CuratorLayout from "../layouts/CuratorLayout";
import PartnerLayout from "../layouts/PartnerLayout";
import ParticipantLayout from "../layouts/ParticipantLayout";

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

    if (role === "participant") {
        return (
            <ParticipantLayout>
                {children}
            </ParticipantLayout>
        );
    }

    // Для остальных (admin, student) – просто children без Layout
    return (
        <>
            {children}
        </>
    );
}