import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from openai import OpenAI
from groq import Groq

# Load environment variables
load_dotenv()

# Feature flag to toggle between OpenAI and Groq
USE_GROQ = os.getenv('USE_GROQ', 'false').lower() == 'true'

# Set up API clients
if USE_GROQ:
    groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    print("Using Groq API with OpenAI fallback")
else:
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    print("Using OpenAI API with Groq fallback")

# Load system prompt from file
def load_system_prompt():
    try:
        with open('prompt.txt', 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        return "You are a helpful Discord bot. Keep responses concise and friendly."
    except Exception as e:
        print(f"Error loading prompt file: {e}")
        return "You are a helpful Discord bot. Keep responses concise and friendly."

system_prompt = load_system_prompt()

# Conversation memory - store conversations per channel
conversation_memory = {}

# Bot setup
intents = discord.Intents.none()
intents.guilds = True
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.event
async def on_message(message):
    print(f'Message received from {message.author}')
    print(f'Message mentions: {message.mentions}')
    print(f'Bot user: {bot.user}')
    print(f'Bot in mentions: {bot.user in message.mentions}')
    
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if the bot is mentioned using mentions list only
    if bot.user in message.mentions:
        print(f'Bot was mentioned!')
        
        # Get the message content without the mention
        content = message.content.replace(f'<@{bot.user.id}>', '').replace(f'<@!{bot.user.id}>', '').strip()
        
        # Get or create conversation history for this channel
        channel_id = str(message.channel.id)
        if channel_id not in conversation_memory:
            conversation_memory[channel_id] = []
        
        # Add user message to conversation history
        conversation_memory[channel_id].append({"role": "user", "content": content})
        
        # Keep only last 10 messages to avoid token limits
        if len(conversation_memory[channel_id]) > 10:
            conversation_memory[channel_id] = conversation_memory[channel_id][-10:]
        
        if content:
            try:
                # Prepare messages with conversation history
                messages = [{"role": "system", "content": system_prompt}] + conversation_memory[channel_id]
                
                # Debug: print conversation history
                print(f"Conversation history for channel {channel_id}:")
                for msg in messages:
                    print(f"  {msg['role']}: {msg['content'][:50]}...")
                
                # Send to AI API with fallback
                response = None
                error_message = ""
                
                # Try primary API first
                try:
                    if USE_GROQ:
                        response = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=messages,
                            max_completion_tokens=300,
                            temperature=0.8
                        )
                    else:
                        response = openai_client.chat.completions.create(
                            model="gpt-4",
                            messages=messages,
                            max_tokens=300,
                            temperature=0.8
                        )
                except Exception as e:
                    primary_api = "Groq" if USE_GROQ else "OpenAI"
                    error_message = f"{primary_api} error: {str(e)}"
                    print(f"Primary API ({primary_api}) failed, trying fallback...")
                    
                    # Try fallback API
                    try:
                        if USE_GROQ:
                            response = openai_client.chat.completions.create(
                                model="gpt-4",
                                messages=messages,
                                max_tokens=300,
                                temperature=0.8
                            )
                        else:
                            response = groq_client.chat.completions.create(
                                model="llama-3.3-70b-versatile",
                                messages=messages,
                                max_completion_tokens=300,
                                temperature=0.8
                            )
                        print("Fallback API succeeded!")
                    except Exception as fallback_e:
                        fallback_api = "OpenAI" if USE_GROQ else "Groq"
                        error_message = f"Both APIs failed. {primary_api}: {str(e)}, {fallback_api}: {str(fallback_e)}"
                        print(f"Fallback API ({fallback_api}) also failed")
                
                if response is None:
                    raise Exception(error_message)
                ai_response = response.choices[0].message.content
                
                # Add bot response to conversation history
                conversation_memory[channel_id].append({"role": "assistant", "content": ai_response})
                
                await message.channel.send(ai_response)
            except Exception as e:
                print(f"All APIs failed: {e}")
                print(f"Error type: {type(e)}")
                await message.channel.send("Sorry, I'm having trouble processing that right now. Please try again later.")
        else:
            await message.channel.send("Hello! How can I help you?")
    
    # Process commands
    await bot.process_commands(message)

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        print("Please create a .env file with your Discord bot token")
        exit(1)
    
    bot.run(token) 