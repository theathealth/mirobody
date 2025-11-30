#!/usr/bin/env python3
"""
Create test users and test API
Complete in one script: create users → configure agents → create profiles → test API calls
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

USER_CONFIGS = [
    {
        "email": "demo_user_alpha@test.com",
        "name": "Test User Alpha",
        "gender": 1,
        "agents": {
            "agent1": {
                "system_prompt": "You are a professional health advisor who excels at analyzing user health data and providing personalized recommendations. Your answers should be based on scientific evidence while considering the user's individual circumstances.",
                "temperature": 0.7,
                "max_tokens": 2000
            }
        },
        "profile": "This is a male user in his 30s who is focused on cardiovascular health and weight management. He hopes to improve his health through scientific methods, including proper diet and regular exercise. The user has a strong interest in health data analysis and seeks personalized health advice."
    },
    {
        "email": "demo_user_beta@test.com",
        "name": "Test User Beta",
        "gender": 2,
        "agents": {
            "agent2": {
                "system_prompt": "You are an experienced health advisor specializing in women's health management and nutritional consulting. You provide comprehensive health advice, including diet, exercise, and lifestyle.",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "agent3": {
                "system_prompt": "You are a professional fitness coach who helps users develop scientific exercise plans and supervises their execution. You provide personalized training programs based on the user's physical condition and goals.",
                "temperature": 0.8,
                "max_tokens": 2500
            }
        },
        "profile": "This is a female user in her 30s who is particularly concerned about women's health, nutritional balance, and mental health. She hopes to maintain a balance between work and life and improve overall well-being through a healthy lifestyle. The user is interested in yoga and aerobic exercise, and also pays attention to dietary nutrition."
    }
]


async def get_db_connection():
    """Get database connection"""
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
    """Create or get user"""
    email = user_config['email']
    name = user_config['name']
    gender = user_config['gender']
    
    # Check if user already exists
    user = await conn.fetchrow('''
        SELECT id, email, name, gender
        FROM theta_ai.health_app_user
        WHERE email = $1 AND is_del = false
    ''', email)
    
    if user:
        print(f"  ℹ️  User already exists: {email} (ID: {user['id']})")
        return user['id']
    
    # Create new user
    user_id = await conn.fetchval('''
        INSERT INTO theta_ai.health_app_user (email, name, gender, is_del)
        VALUES ($1, $2, $3, false)
        RETURNING id
    ''', email, name, gender)
    
    print(f"  ✓ Created successfully: {email} (ID: {user_id})")
    return user_id


async def upsert_user_agents(conn, user_id, agents):
    """Insert or update user agents configuration"""
    await conn.execute('''
        INSERT INTO theta_ai.user_agent_prompt (user_id, prompt, created_at, updated_at)
        VALUES ($1, $2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            prompt = EXCLUDED.prompt,
            updated_at = CURRENT_TIMESTAMP
    ''', str(user_id), json.dumps(agents))
    
    agent_names = ', '.join(agents.keys())
    print(f"  ✓ Agents configuration completed: {agent_names}")


async def upsert_user_profile(conn, user_id, name, profile):
    await conn.execute(f"delete from  theta_ai.health_user_profile_by_system where user_id ='{user_id}'")
    await conn.execute('''
        INSERT INTO theta_ai.health_user_profile_by_system 
            (user_id, name, version, common_part, create_time, last_update_time, is_deleted, last_execute_doc_id)
        VALUES ($1, $2, 1, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, false, 0)
    ''', str(user_id), f'{name} Health Profile', profile)
    
    print(f"  ✓ Health profile created")


def generate_jwt_token(email, user_id):
    """Generate JWT token"""
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
    """Call chat API"""
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
                print(f"  📡 Streaming response:")
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
                                    print(f"\n  ❌ Error: {json.dumps(data['error'], ensure_ascii=False)}")
                                    has_content = True
                            except json.JSONDecodeError:
                                if data_str.strip():
                                    print(data_str, end='', flush=True)
                                    full_content += data_str
                                    has_content = True
                
                print(f"\n  {'─'*50}")
                
                if not has_content:
                    print("  ⚠️  Warning: Received empty response")
                    return None
                
                return {'content': full_content, 'type': 'stream'}
            else:
                # Regular JSON response
                result = response.json()
                print(f"  ✓ Response: {json.dumps(result, ensure_ascii=False)[:100]}...")
                return result
        else:
            print(f"  ❌ API call failed: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return None
    
    except Exception as e:
        print(f"  ❌ Call error: {e}")
        return None


async def process_user(conn, user_config, args):
    """Process single user: create → configure → test"""
    print(f"\n{'='*60}")
    print(f"📝 Processing user: {user_config['name']} ({user_config['email']})")
    print(f"{'='*60}")
    
    try:
        # 1. Create user
        print("\n▶ Creating user account...")
        user_id = await create_or_get_user(conn, user_config)
        
        # 2. Configure agents
        print("\n▶ Configuring user agents...")
        await upsert_user_agents(conn, user_id, user_config['agents'])
        
        # 3. Create health profile
        print("\n▶ Creating health profile...")
        await upsert_user_profile(conn, user_id, user_config['name'], user_config['profile'])
        
        # 4. Generate JWT token
        print("\n▶ Generating JWT token...")
        token = generate_jwt_token(user_config['email'], user_id)
        print(f"  ✓ Token generated successfully (first 50 chars): {token[:50]}...")
        
        # 5. Test API (if not skipped)
        if not args.skip_test:
            print("\n▶ Testing API call...")
            # Get first agent name
            first_agent = list(user_config['agents'].keys())[0]
            print(f"  Agent: {first_agent}")
            print(f"  Question: {args.question}")
            
            result = call_chat_api(token, args.question, first_agent, args.server)
            
            if result:
                print(f"\n  ✅ API test successful!")
            else:
                print(f"\n  ❌ API test failed!")
        
        print(f"\n✅ User {user_config['name']} processing completed!")
        print(f"   ID: {user_id}")
        print(f"   Email: {user_config['email']}")
        print(f"   Agents: {', '.join(user_config['agents'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ User processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    parser = argparse.ArgumentParser(description='Create test users and test API')
    parser.add_argument('--question', '-q', default='Hello, please introduce yourself', help='Test question')
    parser.add_argument('--server', default='http://localhost:18080', help='Server address')
    parser.add_argument('--skip-test', action='store_true', help='Skip API test')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🚀 Creating test users and data")
    print("="*60)
    
    # Connect to database
    try:
        conn = await get_db_connection()
        print("✓ Database connection successful\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    # Process all users
    success_count = 0
    fail_count = 0
    
    for user_config in USER_CONFIGS:
        success = await process_user(conn, user_config, args)
        if success:
            success_count += 1
        else:
            fail_count += 1
    
    # Close connection
    await conn.close()
    
    # Display summary
    print("\n" + "="*60)
    print("📊 Creation completed")
    print("="*60)
    print(f"✅ Successful: {success_count} users")
    if fail_count > 0:
        print(f"❌ Failed: {fail_count} users")
    
    print("\n💡 Next steps:")
    print("   1. Login with the following emails:")
    for user_config in USER_CONFIGS:
        print(f"      - {user_config['email']}")
    print("   2. Verification code: 000000")
    print("   3. Start using the configured agents")
    print()
    
    if fail_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

