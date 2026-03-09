CREATE DATABASE social_sentiment;
use social_sentiment;

-- 用户表
CREATE TABLE users (
    user_id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    platform VARCHAR(100) NOT NULL,
    gender  VARCHAR(40) NOT NULL CHECK(gender IN ('Female', 'Male', 'Unknown')),
    birthday DATE,
    UNIQUE (username, platform),
    INDEX idx_username(username),
    PRIMARY KEY (user_id)
);

-- posts表
CREATE TABLE posts (
    post_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    content TEXT,
    location VARCHAR(255),
    create_time DATETIME,
    content_hash CHAR(32),
    INDEX idx_user(user_id),
    INDEX idx_create_time(create_time),
    INDEX idx_location(location),
    UNIQUE (user_id, content_hash, create_time),
    PRIMARY KEY (post_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- 情感分析表
CREATE TABLE sentiments (
    sentiment_id INT NOT NULL AUTO_INCREMENT,
    post_id INT NOT NULL,
    score DECIMAL(5, 4) NOT NULL,
    type VARCHAR(40) NOT NULL,
    model VARCHAR(40) NOT NULL,
    analysis_time DATETIME NOT NULL,
    INDEX idx_post(post_id),
    PRIMARY KEY (sentiment_id),
    UNIQUE (post_id, model),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

-- 话题表
CREATE TABLE topics (
    topic_id INT NOT NULL AUTO_INCREMENT,
    topic VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    INDEX idx_topic(topic),
    UNIQUE (topic),
    PRIMARY KEY (topic_id)
);

-- 关键词表
CREATE TABLE keywords (
    keyword_id INT NOT NULL AUTO_INCREMENT,
    keyword VARCHAR(100) NOT NULL,
    INDEX idx_keyword(keyword),
    UNIQUE (keyword),
    PRIMARY KEY (keyword_id)
);

-- 多对多关联表
CREATE TABLE posts_topics (
    post_id INT NOT NULL,
    topic_id INT NOT NULL,
    INDEX idx_topic(topic_id),
    PRIMARY KEY (post_id, topic_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
);

CREATE TABLE posts_keywords (
    post_id INT NOT NULL,
    keyword_id INT NOT NULL,
    INDEX idx_keyword(keyword_id),
    PRIMARY KEY (post_id, keyword_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(keyword_id) ON DELETE CASCADE
);

-- 应用系统用户认证/授权表（不同于 users 表中的推文作者）
CREATE TABLE sys_users (
    user_id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username(username),
    PRIMARY KEY (user_id)
);

-- 角色表
CREATE TABLE sys_roles (
    role_id SMALLINT NOT NULL AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    PRIMARY KEY (role_id)
);

-- 用户-角色关系
CREATE TABLE sys_users_roles (
  user_id INT NOT NULL,
  role_id SMALLINT NOT NULL,
  PRIMARY KEY (user_id, role_id),
  FOREIGN KEY (user_id) REFERENCES sys_users(user_id) ON DELETE CASCADE,
  FOREIGN KEY (role_id) REFERENCES sys_roles(role_id) ON DELETE CASCADE
);

-- 初始化常用角色
INSERT INTO sys_roles (name, description) VALUES
    ('admin','系统管理员'),
    ('analyst','数据分析/管理权限'),
    ('ingest','数据查询/导出服务');

-- 初始化管理员用户，密码为admin123
INSERT INTO sys_users (username, password_hash) VALUES
    ('Administer', '$2b$12$1dwwRYIzEqW/1D8HTzsszuSLj62OdxDUzvu6irBTEF4oaY4sOGmni');
INSERT INTO sys_users_roles (user_id, role_id) VALUES
    (1, 1),
    (1, 2),
    (1, 3);