# Kids English Learning App - Architecture Documentation

## 🎯 Project Overview

**Name:** EnglishKids Academy  
**Target Audience:** Children aged 5-12 years  
**Purpose:** Interactive English language learning platform

---

## 📐 System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend (PWA)  │  Mobile Responsive  │  Tablet Support  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API GATEWAY                               │
├─────────────────────────────────────────────────────────────────┤
│  Authentication  │  Rate Limiting  │  Request Routing           │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  User Service  │  Lesson Service  │  Game Service  │  Analytics │
│  Progress Svc  │  Achievement Svc  │  Parent Svc   │  TTS Service│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis Cache  │  S3/MinIO (Media)  │  Elastic    │
└─────────────────────────────────────────────────────────────────┘
```

### Microservices Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Auth Service   │     │  Lesson Service  │     │   Game Service   │
│   (Port: 5001)   │     │   (Port: 5002)   │     │   (Port: 5003)   │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ Progress Service │     │  Parent Service  │     │   TTS Service    │
│   (Port: 5004)   │     │   (Port: 5005)   │     │   (Port: 5006)   │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## 🛠 Technology Stack

### Frontend
| Technology | Purpose | Version |
|------------|---------|---------|
| React 18 | UI Framework | 18.2+ |
| TypeScript | Type Safety | 5.0+ |
| Redux Toolkit | State Management | 2.0+ |
| TailwindCSS | Styling | 3.4+ |
| Framer Motion | Animations | 11.0+ |
| React Router | Navigation | 6.0+ |
| React Query | Data Fetching | 5.0+ |
| Socket.io Client | Real-time | 4.7+ |
| Howler.js | Audio | 2.2+ |
| Konva.js | Canvas Games | 9.0+ |

### Backend
| Technology | Purpose | Version |
|------------|---------|---------|
| Python | Primary Language | 3.11+ |
| FastAPI | API Framework | 0.109+ |
| SQLAlchemy | ORM | 2.0+ |
| Alembic | Migrations | 1.13+ |
| Pydantic | Validation | 2.5+ |
| Celery | Task Queue | 5.3+ |
| Redis | Cache/Broker | 7.2+ |
| JWT | Authentication | - |
| Web Speech API | TTS Integration | - |
| gTTS | Text-to-Speech | 2.3+ |

### Data Storage
| Technology | Purpose |
|------------|---------|
| PostgreSQL 16 | Primary Database |
| Redis | Session Cache, Leaderboards |
| MinIO/S3 | Media Storage |
| Elasticsearch | Search (optional) |

### DevOps & Infrastructure
| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Local Development |
| Nginx | Reverse Proxy |
| GitHub Actions | CI/CD |
| Prometheus | Monitoring |
| Grafana | Dashboards |

---

## 🗄 Database Schema

### Core Tables

```sql
-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(20) NOT NULL DEFAULT 'child', -- child, parent, admin
    avatar_url VARCHAR(500),
    date_of_birth DATE,
    language_preference VARCHAR(10) DEFAULT 'ru',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP
);

CREATE TABLE parent_child_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID REFERENCES users(id) ON DELETE CASCADE,
    child_id UUID REFERENCES users(id) ON DELETE CASCADE,
    relationship VARCHAR(20) DEFAULT 'parent',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(parent_id, child_id)
);

-- Learning Content
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    color VARCHAR(7) DEFAULT '#4CAF50',
    order_index INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE lessons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES categories(id),
    title VARCHAR(200) NOT NULL,
    title_en VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty_level INTEGER DEFAULT 1, -- 1-5
    order_index INTEGER DEFAULT 0,
    estimated_minutes INTEGER DEFAULT 15,
    xp_reward INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vocabulary_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lesson_id UUID REFERENCES lessons(id) ON DELETE CASCADE,
    word VARCHAR(100) NOT NULL,
    translation VARCHAR(200) NOT NULL,
    pronunciation VARCHAR(200),
    image_url VARCHAR(500),
    audio_url VARCHAR(500),
    example_sentence TEXT,
    example_translation TEXT,
    difficulty_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Progress Tracking
CREATE TABLE user_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    lesson_id UUID REFERENCES lessons(id),
    status VARCHAR(20) DEFAULT 'not_started', -- not_started, in_progress, completed
    score INTEGER DEFAULT 0,
    attempts INTEGER DEFAULT 0,
    time_spent_seconds INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, lesson_id)
);

CREATE TABLE vocabulary_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    vocabulary_id UUID REFERENCES vocabulary_items(id) ON DELETE CASCADE,
    mastery_level INTEGER DEFAULT 0, -- 0-5 (SM-2 algorithm)
    ease_factor DECIMAL(4,2) DEFAULT 2.5,
    interval_days INTEGER DEFAULT 0,
    repetitions INTEGER DEFAULT 0,
    next_review_date DATE DEFAULT CURRENT_TIMESTAMP,
    last_review_date DATE,
    correct_count INTEGER DEFAULT 0,
    incorrect_count INTEGER DEFAULT 0,
    UNIQUE(user_id, vocabulary_id)
);

-- Games and Activities
CREATE TABLE games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    game_type VARCHAR(50) NOT NULL, -- matching, quiz, memory, spelling, etc.
    difficulty_levels JSONB,
    config JSONB,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE game_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    game_id UUID REFERENCES games(id),
    lesson_id UUID REFERENCES lessons(id),
    score INTEGER DEFAULT 0,
    max_score INTEGER,
    time_spent_seconds INTEGER,
    correct_answers INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    difficulty_level INTEGER DEFAULT 1,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Achievements and Rewards
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    category VARCHAR(50), -- learning, streak, social, mastery
    requirement_type VARCHAR(50), -- lessons_completed, words_learned, streak_days
    requirement_value INTEGER,
    xp_bonus INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID REFERENCES achievements(id),
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, achievement_id)
);

CREATE TABLE rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    reward_type VARCHAR(50), -- avatar, badge, sticker, theme
    reward_data JSONB,
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Streaks and Daily Goals
CREATE TABLE daily_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    goal_date DATE DEFAULT CURRENT_DATE,
    lessons_target INTEGER DEFAULT 2,
    lessons_completed INTEGER DEFAULT 0,
    words_target INTEGER DEFAULT 10,
    words_learned INTEGER DEFAULT 0,
    minutes_target INTEGER DEFAULT 15,
    minutes_spent INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    UNIQUE(user_id, goal_date)
);

CREATE TABLE streaks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    last_activity_date DATE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tests and Assessments
CREATE TABLE tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    test_type VARCHAR(50), -- placement, lesson, final
    difficulty_level INTEGER,
    time_limit_minutes INTEGER,
    passing_score INTEGER DEFAULT 70,
    questions JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    test_id UUID REFERENCES tests(id),
    score INTEGER,
    total_questions INTEGER,
    correct_answers INTEGER,
    time_spent_seconds INTEGER,
    answers JSONB,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Parent Dashboard
CREATE TABLE parent_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    daily_time_limit_minutes INTEGER DEFAULT 60,
    weekly_reports_enabled BOOLEAN DEFAULT TRUE,
    email_notifications BOOLEAN DEFAULT TRUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    content_restrictions JSONB
);

CREATE TABLE activity_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    activity_data JSONB,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX idx_user_progress_user ON user_progress(user_id);
CREATE INDEX idx_user_progress_lesson ON user_progress(lesson_id);
CREATE INDEX idx_vocabulary_progress_user ON vocabulary_progress(user_id);
CREATE INDEX idx_vocabulary_progress_review ON vocabulary_progress(next_review_date);
CREATE INDEX idx_game_sessions_user ON game_sessions(user_id);
CREATE INDEX idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX idx_activity_logs_date ON activity_logs(created_at);
```

---

## 📦 Functional Modules

### 1. Authentication Module
- Child registration (with parent approval)
- Parent registration and verification
- Secure login with age-appropriate CAPTCHA
- Password recovery via parent email
- Session management
- OAuth integration (Google, Apple)

### 2. User Profile Module
- Avatar customization
- Character selection (guide characters)
- Theme preferences
- Language settings
- Progress visualization
- Achievement showcase

### 3. Learning Module
- Interactive lessons with audio
- Vocabulary flashcards
- Pronunciation practice
- Writing exercises
- Listening comprehension
- Reading exercises

### 4. Game Module
- Word matching games
- Memory games
- Spelling challenges
- Quiz games
- Word search puzzles
- Sentence building
- Story completion

### 5. Progress Module
- Real-time progress tracking
- Learning analytics
- Skill assessment
- Weak area identification
- Personalized recommendations

### 6. Spaced Repetition Module
- SM-2 algorithm implementation
- Review scheduling
- Adaptive difficulty
- Forgetting curve optimization

### 7. Achievement Module
- Badge system
- XP and levels
- Streak rewards
- Special achievements
- Leaderboards (optional)

### 8. Parent Dashboard Module
- Progress overview
- Time spent tracking
- Achievement history
- Learning reports
- Settings management
- Multiple child profiles

### 9. Content Management Module
- Lesson creation
- Vocabulary management
- Media upload
- Content versioning
- Translation management

---

## 🎮 Game Examples

### 1. Word Match Game
```json
{
  "game_type": "matching",
  "name": "Word Match",
  "description": "Match English words with their translations",
  "config": {
    "grid_size": 4,
    "time_limit": 60,
    "points_per_match": 10,
    "bonus_time": 5
  }
}
```

### 2. Memory Cards
```json
{
  "game_type": "memory",
  "name": "Memory Cards",
  "description": "Find matching pairs of words and images",
  "config": {
    "pairs_count": 8,
    "flip_time": 1000,
    "show_hint_after": 3
  }
}
```

### 3. Spelling Bee
```json
{
  "game_type": "spelling",
  "name": "Spelling Bee",
  "description": "Listen and spell the word correctly",
  "config": {
    "word_count": 10,
    "hints_allowed": 2,
    "time_per_word": 30
  }
}
```

### 4. Sentence Builder
```json
{
  "game_type": "sentence_builder",
  "name": "Build a Sentence",
  "description": "Arrange words to form correct sentences",
  "config": {
    "sentences_count": 5,
    "show_translation": true,
    "time_limit": 120
  }
}
```

### 5. Picture Quiz
```json
{
  "game_type": "picture_quiz",
  "name": "What's This?",
  "description": "Identify objects from pictures",
  "config": {
    "questions_count": 10,
    "options_count": 4,
    "time_per_question": 15
  }
}
```

---

## 🔒 Security Requirements

### COPPA Compliance (Children's Online Privacy Protection Act)

1. **Parental Consent**
   - Verifiable parental consent before collecting data
   - Parent approval for account creation
   - Email verification for parents

2. **Data Minimization**
   - Collect only necessary data
   - No collection of precise geolocation
   - No behavioral advertising

3. **Data Protection**
   - Encryption at rest (AES-256)
   - Encryption in transit (TLS 1.3)
   - Secure password hashing (bcrypt/argon2)
   - Regular security audits

4. **Access Controls**
   - Role-based access control (RBAC)
   - Session timeout for inactivity
   - Secure API endpoints
   - Rate limiting

5. **Privacy Features**
   - No social features without parental approval
   - No public profiles
   - Data deletion on request
   - Transparent privacy policy

### Technical Security Measures

```python
# Example security configuration
SECURITY_CONFIG = {
    "password_hashing": {
        "algorithm": "argon2",
        "time_cost": 3,
        "memory_cost": 65536,
        "parallelism": 4
    },
    "session": {
        "max_age_minutes": 30,
        "inactivity_timeout_minutes": 15,
        "secure_cookie": True,
        "httponly": True,
        "samesite": "strict"
    },
    "rate_limiting": {
        "login_attempts": 5,
        "lockout_minutes": 15,
        "api_requests_per_minute": 60
    },
    "encryption": {
        "algorithm": "AES-256-GCM",
        "key_rotation_days": 90
    }
}
```

---

## 🎨 UI/UX Guidelines

### Design Principles

1. **Age-Appropriate Design**
   - Large, tappable buttons (min 44x44px)
   - Clear visual hierarchy
   - Minimal text, maximum visuals
   - Intuitive navigation

2. **Color Palette**
   ```
   Primary: #6C63FF (Purple - friendly, creative)
   Secondary: #FF6B6B (Coral - energetic, warm)
   Success: #4CAF50 (Green - positive feedback)
   Warning: #FFB74D (Orange - attention)
   Background: #F8F9FA (Light gray - easy on eyes)
   ```

3. **Typography**
   - Primary: Nunito (rounded, friendly)
   - Secondary: Comic Neue (playful)
   - Size: Minimum 16px for body text

4. **Animations**
   - Smooth transitions (300ms)
   - Celebratory animations for achievements
   - Character animations for engagement
   - Progress animations

### Character Guides

1. **Owl Professor "Hoot"** - Learning guide
2. **Fox "Felix"** - Game companion
3. **Rabbit "Ruby"** - Achievement celebrator
4. **Bear "Bruno"** - Encouragement friend

### Engagement Strategies

1. **Gamification**
   - XP points for activities
   - Levels and ranks
   - Daily challenges
   - Weekly quests

2. **Positive Reinforcement**
   - Immediate feedback
   - Celebration animations
   - Encouraging messages
   - Progress celebrations

3. **Personalization**
   - Customizable avatars
   - Theme selection
   - Character companions
   - Learning path choices

4. **Social Features (Parent-Controlled)**
   - Family leaderboards
   - Achievement sharing
   - Group challenges

---

## 📱 Responsive Design Breakpoints

```css
/* Mobile First Approach */
/* Small phones */
@media (min-width: 320px) { }

/* Large phones */
@media (min-width: 480px) { }

/* Tablets */
@media (min-width: 768px) { }

/* Small laptops */
@media (min-width: 1024px) { }

/* Desktops */
@media (min-width: 1280px) { }
```

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CDN (CloudFlare)                        │
│  Static Assets │ SSL │ DDoS Protection │ Caching            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                     │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  App Server 1 │   │  App Server 2 │   │  App Server N │
│   (FastAPI)   │   │   (FastAPI)   │   │   (FastAPI)   │
└───────────────┘   └───────────────┘   └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│  PostgreSQL   │   │    Redis      │   │    MinIO      │
│   (Primary)   │   │   (Cache)     │   │   (Media)     │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## 📊 Monitoring & Analytics

### Key Metrics

1. **Engagement Metrics**
   - Daily Active Users (DAU)
   - Session duration
   - Lessons completed
   - Games played

2. **Learning Metrics**
   - Words learned
   - Accuracy rates
   - Progress speed
   - Retention rates

3. **Technical Metrics**
   - API response times
   - Error rates
   - Database performance
   - Cache hit rates

---

## 🔄 API Endpoints Overview

### Authentication
- `POST /api/auth/register/child`
- `POST /api/auth/register/parent`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`
- `POST /api/auth/forgot-password`

### Users
- `GET /api/users/me`
- `PUT /api/users/me`
- `GET /api/users/me/progress`
- `GET /api/users/me/achievements`

### Lessons
- `GET /api/lessons`
- `GET /api/lessons/{id}`
- `GET /api/lessons/{id}/vocabulary`
- `POST /api/lessons/{id}/start`
- `POST /api/lessons/{id}/complete`

### Games
- `GET /api/games`
- `GET /api/games/{id}`
- `POST /api/games/{id}/start`
- `POST /api/games/{id}/finish`

### Progress
- `GET /api/progress/overview`
- `GET /api/progress/vocabulary`
- `GET /api/progress/reviews`
- `POST /api/progress/review`

### Parent
- `GET /api/parent/children`
- `GET /api/parent/children/{id}/progress`
- `GET /api/parent/children/{id}/reports`
- `PUT /api/parent/settings`

---

## 📅 Development Phases

### Phase 1: Foundation (Weeks 1-4)
- Project setup
- Database design
- Authentication system
- Basic UI framework

### Phase 2: Core Features (Weeks 5-8)
- Lesson system
- Vocabulary management
- Flashcard module
- Basic games

### Phase 3: Engagement (Weeks 9-12)
- Achievement system
- Progress tracking
- Spaced repetition
- Character guides

### Phase 4: Parent Features (Weeks 13-16)
- Parent dashboard
- Progress reports
- Settings management
- Notifications

### Phase 5: Polish & Launch (Weeks 17-20)
- Testing
- Performance optimization
- Security audit
- Deployment
