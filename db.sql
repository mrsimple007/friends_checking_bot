-- SQL Schema for Telegram Bot Database (Supabase/PostgreSQL)

-- ============================================================
-- TABLE: users
-- Stores user information and preferences
-- ============================================================
CREATE TABLE IF NOT EXISTS friends_users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(255),
    language VARCHAR(5) DEFAULT 'en',
    is_premium BOOLEAN DEFAULT FALSE,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast telegram_id lookups
CREATE INDEX idx_users_telegram_id ON friends_users(telegram_id);

-- ============================================================
-- TABLE: birthdays
-- Stores birthday information for each user
-- ============================================================
CREATE TABLE IF NOT EXISTS birthdays (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    day INTEGER NOT NULL CHECK (day >= 1 AND day <= 31),
    month INTEGER NOT NULL CHECK (month >= 1 AND month <= 12),
    year INTEGER CHECK (year >= 1900 AND year <= 2100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key to users table
    CONSTRAINT fk_birthday_user 
        FOREIGN KEY (user_id) 
        REFERENCES friends_users(telegram_id) 
        ON DELETE CASCADE
);

-- Indexes for efficient queries
CREATE INDEX idx_birthdays_user_id ON birthdays(user_id);
CREATE INDEX idx_birthdays_date ON birthdays(month, day);

-- ============================================================
-- TABLE: tests
-- Stores friendship tests created by users
-- ============================================================
CREATE TABLE IF NOT EXISTS tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key to users table
    CONSTRAINT fk_test_user 
        FOREIGN KEY (user_id) 
        REFERENCES friends_users(telegram_id) 
        ON DELETE CASCADE
);

-- Index for fast user_id lookups
CREATE INDEX idx_tests_user_id ON tests(user_id);
CREATE INDEX idx_tests_active ON tests(is_active);

-- ============================================================
-- TABLE: test_answers_owner
-- Stores the test creator's answers
-- ============================================================
CREATE TABLE IF NOT EXISTS test_answers_owner (
    id BIGSERIAL PRIMARY KEY,
    test_id UUID NOT NULL,
    question_index INTEGER NOT NULL CHECK (question_index >= 0 AND question_index < 15),
    answer_index INTEGER NOT NULL CHECK (answer_index >= 0 AND answer_index < 4),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key to tests table
    CONSTRAINT fk_answer_owner_test 
        FOREIGN KEY (test_id) 
        REFERENCES tests(id) 
        ON DELETE CASCADE,
    
    -- Ensure one answer per question per test
    UNIQUE(test_id, question_index)
);

-- Index for fast test_id lookups
CREATE INDEX idx_answers_owner_test_id ON test_answers_owner(test_id);

-- ============================================================
-- TABLE: test_results
-- Stores results from friends who take the test
-- ============================================================
CREATE TABLE IF NOT EXISTS test_results (
    id BIGSERIAL PRIMARY KEY,
    test_id UUID NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key to tests table
    CONSTRAINT fk_result_test 
        FOREIGN KEY (test_id) 
        REFERENCES tests(id) 
        ON DELETE CASCADE,
    
    -- Ensure one result per user per test
    UNIQUE(test_id, user_id)
);

-- Indexes for efficient queries
CREATE INDEX idx_results_test_id ON test_results(test_id);
CREATE INDEX idx_results_user_id ON test_results(user_id);

-- ============================================================
-- TABLE: premium_subscriptions
-- Tracks premium subscriptions
-- ============================================================
CREATE TABLE IF NOT EXISTS premium_subscriptions (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL UNIQUE,
    subscription_type VARCHAR(50) DEFAULT 'monthly',
    start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_date TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    payment_method VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key to users table
    CONSTRAINT fk_subscription_user 
        FOREIGN KEY (user_id) 
        REFERENCES friends_users(telegram_id) 
        ON DELETE CASCADE
);

-- Index for fast user_id lookups
CREATE INDEX idx_subscriptions_user_id ON premium_subscriptions(user_id);
CREATE INDEX idx_subscriptions_active ON premium_subscriptions(is_active);

-- ============================================================
-- TABLE: bot_analytics
-- Stores analytics and usage statistics
-- ============================================================
CREATE TABLE IF NOT EXISTS bot_analytics (
    id BIGSERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    event_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for analytics queries
CREATE INDEX idx_analytics_event_type ON bot_analytics(event_type);
CREATE INDEX idx_analytics_user_id ON bot_analytics(user_id);
CREATE INDEX idx_analytics_created_at ON bot_analytics(created_at);

-- ============================================================
-- FUNCTIONS: Update timestamp on row update
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON friends_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_birthdays_updated_at
    BEFORE UPDATE ON birthdays
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tests_updated_at
    BEFORE UPDATE ON tests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at
    BEFORE UPDATE ON premium_subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- ROW LEVEL SECURITY (RLS) - Optional
-- Enable if you want user-specific access control
-- ============================================================

-- Enable RLS on tables
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE birthdays ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE tests ENABLE ROW LEVEL SECURITY;

-- Example RLS policies (uncomment to use)
-- CREATE POLICY "Users can view own data" ON users
--     FOR SELECT USING (telegram_id = current_setting('app.current_user_id'));

-- CREATE POLICY "Users can view own birthdays" ON birthdays
--     FOR ALL USING (user_id = current_setting('app.current_user_id'));

-- ============================================================
-- SAMPLE DATA (for testing)
-- ============================================================

-- Uncomment to insert sample data for testing
/*
INSERT INTO users (telegram_id, username, language, is_premium) 
VALUES 
    ('123456789', 'test_user', 'en', FALSE),
    ('987654321', 'premium_user', 'uz', TRUE);

INSERT INTO birthdays (user_id, name, day, month, year) 
VALUES 
    ('123456789', 'Aziza', 12, 3, NULL),
    ('123456789', 'John', 15, 7, 1995);
*/

-- ============================================================
-- USEFUL QUERIES
-- ============================================================

-- Get all birthdays for today
-- SELECT b.*, u.telegram_id, u.language 
-- FROM birthdays b
-- JOIN users u ON b.user_id = u.telegram_id
-- WHERE b.day = EXTRACT(DAY FROM CURRENT_DATE)
--   AND b.month = EXTRACT(MONTH FROM CURRENT_DATE);

-- Get birthday count for a user
-- SELECT COUNT(*) FROM birthdays WHERE user_id = '123456789';

-- Get test results summary
-- SELECT 
--     t.id,
--     t.user_id,
--     COUNT(r.id) as total_takers,
--     AVG(r.score) as avg_score
-- FROM tests t
-- LEFT JOIN test_results r ON t.id = r.test_id
-- WHERE t.user_id = '123456789'
-- GROUP BY t.id, t.user_id;

-- ============================================================
-- MAINTENANCE QUERIES
-- ============================================================

-- Delete inactive tests older than 30 days
-- DELETE FROM tests 
-- WHERE is_active = FALSE 
--   AND created_at < NOW() - INTERVAL '30 days';

-- Archive old analytics data
-- DELETE FROM bot_analytics 
-- WHERE created_at < NOW() - INTERVAL '90 days';