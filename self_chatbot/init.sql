-- Multi-LLM Chat Database Schema
-- Create chat sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(255) NOT NULL DEFAULT 'New Chat',
    model_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_favorite BOOLEAN DEFAULT FALSE
);

-- Create chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('user', 'assistant')),
    content TEXT NOT NULL,
    image_data TEXT, -- Base64 encoded image data
    image_type VARCHAR(50), -- image/png, image/jpeg, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    model_name VARCHAR(100)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_chat_sessions_created_at ON chat_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_favorite ON chat_sessions(is_favorite, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON chat_messages(session_id, created_at);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE OR REPLACE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data (optional)
INSERT INTO chat_sessions (session_name, model_name) 
VALUES 
    ('Welcome Chat', 'gpt-4'),
    ('Test Session', 'claude-3-sonnet')
ON CONFLICT DO NOTHING;

INSERT INTO chat_messages (session_id, message_type, content, model_name)
VALUES 
    (1, 'user', 'Hello! How can I use this Multi-LLM Chat app?', 'gpt-4'),
    (1, 'assistant', 'Welcome to Multi-LLM Chat! You can switch between different AI models like GPT-4, Claude, and Gemini to have conversations. Just select your preferred model and start chatting!', 'gpt-4'),
    (2, 'user', 'What models are available?', 'claude-3-sonnet'),
    (2, 'assistant', 'This app supports multiple LLM providers including Azure OpenAI (GPT models), Google Gemini, and AWS Claude. You can easily switch between them using the model selector.', 'claude-3-sonnet')
ON CONFLICT DO NOTHING;