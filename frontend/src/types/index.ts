export type User = {
    id: string;
    email: string;
    full_name: string;
    organization_id: string;
    role: string;
};

export type Contractor = {
    id: string;
    name: string;
    email?: string;
    phone?: string;
    company_name?: string;
    service_type?: string;
    payment_mode?: string;
    is_active: boolean;
};

export type Task = {
    id: string;
    title: string;
    description?: string;
    status: "pending" | "in_progress" | "completed" | "cancelled";
    priority: "low" | "medium" | "high" | "urgent";
    due_date?: string;
    organization_id: string;
    created_by: string;
    created_at: string;
    assignments: TaskAssignment[];
    contractor_id?: string;
    transaction_id?: string;
    target_role?: string;
};

export type TaskAssignment = {
    user_id: string;
    user?: User; // joined
    assigned_at: string;
};

export type Reminder = {
    id: string;
    title: string;
    message: string;
    scheduled_for: string;
    status: "pending" | "sent" | "dismissed";
    reminder_type: "system" | "personal" | "meeting" | "payment";
};
