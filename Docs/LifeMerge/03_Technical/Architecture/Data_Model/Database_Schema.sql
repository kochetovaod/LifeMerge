-- LifeMerge core schema (PostgreSQL)

CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    is_pro BOOLEAN NOT NULL DEFAULT false,
    trial_end TIMESTAMPTZ,
    full_name TEXT,
    timezone TEXT NOT NULL DEFAULT 'UTC',
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE goals (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT,
    deadline TIMESTAMPTZ,
    progress NUMERIC(5,2) DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_id UUID REFERENCES goals(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT,
    context TEXT,
    energy_level TEXT CHECK (energy_level IN ('light','medium','heavy')),
    estimated_minutes INTEGER,
    priority TEXT DEFAULT 'P2' CHECK (priority IN ('P0','P1','P2')),
    deadline TIMESTAMPTZ,
    is_recurring BOOLEAN NOT NULL DEFAULT false,
    recurrence_rule TEXT,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','done','canceled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE subtasks (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT false,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE finance_categories (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('income','expense')),
    color TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE finance_transactions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES finance_categories(id) ON DELETE SET NULL,
    type TEXT NOT NULL CHECK (type IN ('income','expense')),
    linked_event_id UUID,
    is_recurring BOOLEAN NOT NULL DEFAULT false,
    recurrence_rule TEXT,
    amount NUMERIC(14,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    happened_at TIMESTAMPTZ NOT NULL,
    transaction_date TIMESTAMPTZ NOT NULL DEFAULT now(),
    note TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE calendar_events (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL CHECK (type IN ('event','task_block','finance_event')),
    linked_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    linked_finance_id UUID REFERENCES finance_transactions(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    location TEXT,
    source TEXT DEFAULT 'lifemerge',
    category TEXT,
    recurrence_rule TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE inbox_items (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT,
    type TEXT NOT NULL CHECK (type IN ('idea','task','goal','finance')),
    source TEXT, -- email, widget, integration
    payload JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','processed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE budgets (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES finance_categories(id) ON DELETE SET NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    limit_amount NUMERIC(14,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'USD'
);

CREATE TABLE ai_plans (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_json JSONB NOT NULL,
    prompt_version TEXT,
    model_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tasks_user_deadline ON tasks(user_id, deadline);
CREATE INDEX idx_events_user_start ON calendar_events(user_id, start_time);
CREATE INDEX idx_fin_tx_user_date ON finance_transactions(user_id, happened_at);
