#!/usr/bin/env python3
"""
创建测试用户并测试 API
在一个脚本中完成：创建用户 → 配置 agents → 创建档案 → 调用 API 测试
"""

import argparse
import asyncio
import asyncpg
import jwt
import json
import time
import requests
import yaml
import sys

# Hardcoded JWT key (should match config.optional.yaml)
# Decrypted from: gAAAAABpJiizBb7BmtHTYPTQc7kcKb8qNulxcTcOCPXxXw2zPo6w4H-QCb-htLdQMZl0ZuFFZx2y0jzwZufZ3Nz6s0DvkI7G6A==
HARDCODED_JWT_KEY = "myjwtkey"


# CREATE TABLE IF NOT EXISTS theta_ai.user_agent_prompt (
#     id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
#     user_id VARCHAR(255) NOT NULL UNIQUE,
#     prompt JSONB NOT NULL DEFAULT '{}'::jsonb,
#     created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
#     updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
# );

# CREATE INDEX IF NOT EXISTS idx_user_agent_prompt_user_id ON theta_ai.user_agent_prompt(user_id);

# ============================================================
# 用户配置 - 每个用户的所有信息组织在一起
# ============================================================

USER_CONFIGS = [
    {
        "email": "demo_user_alpha@test.com",
        "name": "测试用户Alpha",
        "gender": 1,
        "agents": {
            "agent1": {
                "system_prompt": "你是一位专业的健康顾问，擅长分析用户的健康数据并提供个性化建议。你的回答应该基于科学依据，同时考虑用户的个人情况。",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        },
        "profile": "这是一位30多岁的男性用户，关注心血管健康和体重管理。他希望通过科学的方式改善健康状况，包括合理饮食和规律运动。用户对健康数据分析有浓厚兴趣，希望获得个性化的健康建议。"
    },
    {
        "email": "demo_user_beta@test.com",
        "name": "测试用户Beta",
        "gender": 2,
        "agents": {
            "agent2": {
                "system_prompt": "你是一位经验丰富的健康顾问，专注于女性健康管理和营养咨询。你会提供全面的健康建议，包括饮食、运动和生活方式。",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "agent3": {
                "system_prompt": "你是一位专业的健身教练，帮助用户制定科学的运动计划并监督执行。你会根据用户的身体状况和目标提供个性化的训练方案。",
                "temperature": 0.8,
                "max_tokens": 2500
            }
        },
        "profile": "这是一位30多岁的女性用户，特别关注女性健康、营养均衡和心理健康。她希望在工作和生活之间保持平衡，通过健康的生活方式提升整体福祉。用户对瑜伽和有氧运动感兴趣，也注重饮食营养。"
    }
]


async def get_db_connection():
    """获取数据库连接"""
    # Load config
    config = {}
    for config_file in ['config.required.yaml', 'config.optional.yaml']:
        try:
            with open(config_file, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config.update(file_config)
        except FileNotFoundError:
            pass
    
    # Database connection
    pg_host = config.get('PG_HOST', 'localhost')
    if pg_host == 'db':
        pg_host = 'localhost'  # Use localhost when running outside Docker
    
    pg_password = config.get('PG_PASSWORD', 'holistic_password')
    if isinstance(pg_password, str) and pg_password.startswith('gAAAAAB'):
        # Encrypted password, use Docker default
        pg_password = 'holistic_password'
    
    conn = await asyncpg.connect(
        host=pg_host,
        port=config.get('PG_PORT', 5432),
        user=config.get('PG_USER', 'holistic_user'),
        password=pg_password,
        database=config.get('PG_DBNAME', 'holistic_db')
    )
    
    return conn


async def create_or_get_user(conn, user_config):
    """创建或获取用户"""
    email = user_config['email']
    name = user_config['name']
    gender = user_config['gender']
    
    # 检查用户是否已存在
    user = await conn.fetchrow('''
        SELECT id, email, name, gender
        FROM theta_ai.health_app_user
        WHERE email = $1 AND is_del = false
    ''', email)
    
    if user:
        print(f"  ℹ️  用户已存在: {email} (ID: {user['id']})")
        return user['id']
    
    # 创建新用户
    user_id = await conn.fetchval('''
        INSERT INTO theta_ai.health_app_user (email, name, gender, is_del)
        VALUES ($1, $2, $3, false)
        RETURNING id
    ''', email, name, gender)
    
    print(f"  ✓ 创建成功: {email} (ID: {user_id})")
    return user_id


async def upsert_user_agents(conn, user_id, agents):
    """插入或更新用户 agents 配置"""
    await conn.execute('''
        INSERT INTO theta_ai.user_agent_prompt (user_id, prompt, created_at, updated_at)
        VALUES ($1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            prompt = EXCLUDED.prompt,
            updated_at = CURRENT_TIMESTAMP
    ''', str(user_id), json.dumps(agents))
    
    agent_names = ', '.join(agents.keys())
    print(f"  ✓ Agents配置完成: {agent_names}")


async def upsert_user_profile(conn, user_id, name, profile):
    await conn.execute(f"delete from  theta_ai.health_user_profile_by_system where user_id ='{user_id}'")
    await conn.execute('''
        INSERT INTO theta_ai.health_user_profile_by_system 
            (user_id, name, version, common_part, create_time, last_update_time, is_deleted, last_execute_doc_id)
        VALUES ($1, $2, 1, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, false, 0)
    ''', str(user_id), f'{name}健康档案', profile)
    
    print(f"  ✓ 健康档案已创建")


def generate_jwt_token(email, user_id):
    """生成 JWT token"""
    jwt_key = HARDCODED_JWT_KEY
    
    payload = {
        'sub': email,
        'user_id': str(user_id),
        'iss': 'theta_oauth',
        'aud': 'theta',
        'iat': int(time.time()),
        'exp': int(time.time()) + 3600
    }
    
    token = jwt.encode(payload, jwt_key, algorithm='HS256')
    return token


def call_chat_api(token, question, agent_name, server='http://localhost:18080'):
    """调用 chat API"""
    url = f"{server}/api/chat"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    payload = {
        'question': question,
        'prompt_name': agent_name
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60, stream=True)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            
            # Check if it's a streaming response (SSE)
            if 'text/event-stream' in content_type or 'stream' in content_type.lower():
                print(f"  📡 流式响应:")
                print(f"  {'─'*50}")
                full_content = ""
                has_content = False
                
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        # SSE format: data: {...}
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            try:
                                data = json.loads(data_str)
                                if 'content' in data and data['content']:
                                    print(data['content'], end='', flush=True)
                                    full_content += data['content']
                                    has_content = True
                                elif 'delta' in data and 'content' in data['delta']:
                                    content = data['delta']['content']
                                    if content:
                                        print(content, end='', flush=True)
                                        full_content += content
                                        has_content = True
                                elif 'error' in data:
                                    print(f"\n  ❌ 错误: {json.dumps(data['error'], ensure_ascii=False)}")
                                    has_content = True
                            except json.JSONDecodeError:
                                if data_str.strip():
                                    print(data_str, end='', flush=True)
                                    full_content += data_str
                                    has_content = True
                
                print(f"\n  {'─'*50}")
                
                if not has_content:
                    print("  ⚠️  警告: 收到空响应")
                    return None
                
                return {'content': full_content, 'type': 'stream'}
            else:
                # Regular JSON response
                result = response.json()
                print(f"  ✓ 响应: {json.dumps(result, ensure_ascii=False)[:100]}...")
                return result
        else:
            print(f"  ❌ API 调用失败: {response.status_code}")
            print(f"  响应: {response.text[:200]}")
            return None
    
    except Exception as e:
        print(f"  ❌ 调用错误: {e}")
        return None


async def process_user(conn, user_config, args):
    """处理单个用户：创建 → 配置 → 测试"""
    print(f"\n{'='*60}")
    print(f"📝 处理用户: {user_config['name']} ({user_config['email']})")
    print(f"{'='*60}")
    
    try:
        # 1. 创建用户
        print("\n▶ 创建用户账号...")
        user_id = await create_or_get_user(conn, user_config)
        
        # 2. 配置 agents
        print("\n▶ 配置用户 agents...")
        await upsert_user_agents(conn, user_id, user_config['agents'])
        
        # 3. 创建健康档案
        print("\n▶ 创建健康档案...")
        await upsert_user_profile(conn, user_id, user_config['name'], user_config['profile'])
        
        # 4. 生成 JWT token
        print("\n▶ 生成 JWT token...")
        token = generate_jwt_token(user_config['email'], user_id)
        print(f"  ✓ Token 生成成功 (前50字符): {token[:50]}...")
        
        # 5. 测试 API（如果不跳过）
        if not args.skip_test:
            print("\n▶ 测试 API 调用...")
            # 获取第一个 agent 名称
            first_agent = list(user_config['agents'].keys())[0]
            print(f"  Agent: {first_agent}")
            print(f"  问题: {args.question}")
            
            result = call_chat_api(token, args.question, first_agent, args.server)
            
            if result:
                print(f"\n  ✅ API 测试成功!")
            else:
                print(f"\n  ❌ API 测试失败!")
        
        print(f"\n✅ 用户 {user_config['name']} 处理完成!")
        print(f"   ID: {user_id}")
        print(f"   邮箱: {user_config['email']}")
        print(f"   Agents: {', '.join(user_config['agents'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 处理用户失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    parser = argparse.ArgumentParser(description='创建测试用户并测试 API')
    parser.add_argument('--question', '-q', default='你好，介绍一下你自己', help='测试问题')
    parser.add_argument('--server', default='http://localhost:18080', help='服务器地址')
    parser.add_argument('--skip-test', action='store_true', help='跳过 API 测试')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🚀 创建测试用户和数据")
    print("="*60)
    
    # 连接数据库
    try:
        conn = await get_db_connection()
        print("✓ 数据库连接成功\n")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        sys.exit(1)
    
    # 处理所有用户
    success_count = 0
    fail_count = 0
    
    for user_config in USER_CONFIGS:
        success = await process_user(conn, user_config, args)
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # 关闭连接
    await conn.close()
    
    # 显示总结
    print("\n" + "="*60)
    print("📊 创建完成")
    print("="*60)
    print(f"✅ 成功: {success_count} 个用户")
    if fail_count > 0:
        print(f"❌ 失败: {fail_count} 个用户")
    
    print("\n💡 下一步:")
    print("   1. 使用以下邮箱登录:")
    for user_config in USER_CONFIGS:
        print(f"      - {user_config['email']}")
    print("   2. 验证码: 000000")
    print("   3. 开始使用配置的 agents")
    print()
    
    if fail_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

