from django.shortcuts import render, redirect
import os
import io
from django.http import HttpResponse
from django.http import JsonResponse
import csv
import json
from openai import OpenAI
from dotenv import load_dotenv
import anthropic
from django.views.decorators.csrf import csrf_exempt
from .models import *
import httpx
import openai
from openai import OpenAIError, AuthenticationError, RateLimitError, APIConnectionError
from django.contrib.auth.decorators import login_required
import csv
from django.contrib import messages

# from openai import openai.error.AuthenticationError, openai.error.InvalidRequestError



load_dotenv()
# OPENAI_API_KEY = ""
# ANTHROPIC_API_KEY = ""

def get_api_key(choice):
    setting_page_obj = SettingPage.objects.first()
    ANTHROPIC_API_KEY = setting_page_obj.Claude_API
    OPENAI_API_KEY = setting_page_obj.OpenAI_API

    if choice == "OpenAI":
        return OPENAI_API_KEY
    elif choice == "Claude":
        return ANTHROPIC_API_KEY
    else:
        raise ValueError("Invalid AI choice.")

def generate_openai_variants(api_key, prompt, temperature, presence_penalty, frequency_penalty, system_prompt):
    client = OpenAI(api_key=api_key)
    # OpenAI.api_key = api_key
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=temperature,
        presence_penalty=presence_penalty,
        frequency_penalty=frequency_penalty,
        n=3
    )
    # print("Response is: ", response)
    variants = [choice.message.content.strip() for choice in response.choices]
    return variants
    

def generate_claude_variants(api_key, prompt, temperature, system_prompt):
    # client = httpx.Client(verify=False)
    client = anthropic.Anthropic(api_key=api_key)
    messages = []
    print("system prompt in claude ", system_prompt)
    for i in range(3):
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            system= system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature= temperature,
            timeout=3000
        )
        messages.append(message.content[0].text)
    return messages

def create_combined_prompt(memory, user_prompt, person_choice, paragraph_length):
    if person_choice.lower() == 'i':
        instruction = "Always speak intimately to the reader in a first person singular voice, e.g. 'I'. Do not talk about people in the abstract, instead, address the reader intimately as 'you'. Do not use words like 'one’s' or 'oneself.' Always use I, me, myself."
    elif person_choice.lower() == 'you':
        instruction = "Always speak intimately to the reader in second person singular, e.g. 'you'. Do not talk about people in the abstract, instead, address the reader intimately as 'you'. Do not use words like 'one’s' or 'oneself.' Do not use 'we' or 'us' or 'our'."
    elif person_choice.lower() == 'we':
        instruction = "Always speak intimately to the reader in a first person plural voice, e.g. 'We'. Do not talk about people in the abstract, instead, address the reader intimately as 'you'. Do not use words like 'one’s' or 'oneself.' Always use we, our, us."
    else:
        raise ValueError("Invalid person choice.")
    
    paragraph = f"Length of the generated output should be {paragraph_length} words. Vary sentence structure of 5-20 words so there's a nice variety, using short sentences to make a dramatic rhetorical point."

    combined_prompt = f"{instruction}\n\n{memory}\n\n{user_prompt}\n\n{paragraph_length}\n\n{paragraph}"
    return combined_prompt


@login_required(login_url="myauth:loginPage")
def promptActionPage(request):
    memory = request.session.get('memory', [])
    if not isinstance(memory, list):
        memory = []

    instructions_set = InstructionsSet.objects.all()
    instructions_data = []
    instructions_theme = InstructionsTheme.objects.all()
    instructions_data_theme = []


    for instruction_set in instructions_set:
        instructions = instruction_set.instructions.all()
        instructions_data.append({
            'set_id': instruction_set.id,
            'set_name': instruction_set.name,
            'instructions': [{'id': instr.id, 'name': instr.name, 'text': instr.text} for instr in instructions]
        })

    for instruction_theme in instructions_theme:
        instructions = instruction_theme.instructionsThemeRow.all()
        instructions_data_theme.append({
            'set_id': instruction_theme.id,
            'set_name': instruction_theme.name,
            'instructions': [{'id': instr.id, 'name': instr.name, 'text': instr.text} for instr in instructions]
        })

    print(" themes are ", instructions_theme)
    print(" instructions_set are ", instructions_set)
    memory_json = json.dumps(memory)
    context = {
        'memory_array': memory_json,
        'instructions_set': instructions_set,
        'instructions_data': json.dumps(instructions_data),  # Convert to JSON for easy access in JS
        'instructions_theme': instructions_theme,
        'instructions_data_theme': json.dumps(instructions_data_theme)
    }
    return render(request, 'promptapp/promptHome.html', context)


@login_required(login_url="myauth:loginPage")
def instructions_set(request):
    memory = request.session.get('memory', [])
    if not isinstance(memory, list):
                memory = []
    instructions_set = InstructionsSet.objects.all()
    instructions_data = [
        {
            'set_id': instruction_set.id,
            'set_name': instruction_set.name,
            'instructions': list(instruction_set.instructions.values('id', 'name','text'))
        }
        for instruction_set in instructions_set
    ]
    instructions_json = json.dumps(instructions_data)
    memory_json = json.dumps(memory)
    print("instructions_set: ", instructions_json)
    print("memory_json: ", memory_json)
    context = {
        'memory_array': memory_json,
        'instructions_set': instructions_set,
        'instructions_data': instructions_json,

    }
    return render(request, 'promptapp/instructionsset.html', context)


# views.py
@csrf_exempt
def save_or_edit_instruction(request):
    if request.method == 'POST':
        # print("request post : ", (request.POST))
        instruction_id = request.POST.get('instruction_id')  # For editing, this will be provided
        if instruction_id:
            instruction_id = int(instruction_id)
        else:
            instruction_id = ""  # or set it to some default value
        # print("instruction_id : ", instruction_id)
        instruction_set_name = request.POST.get('instruction_set_name')
        instructions = json.loads(request.POST.get('instructions', '[]'))
        
        # Create new InstructionsSet

        if instruction_id:  # If instruction_id is provided, it means we are editing existing instruction
            try:
                instruction_set = InstructionsSet.objects.get(id=instruction_id)
                instruction_set.name = instruction_set_name
                instruction_set.save()

                Instruction.objects.filter(instruction_set_id=instruction_id).delete()

                for instr in instructions:
                    instruction_obj_new = Instruction.objects.create(
                        instruction_set=instruction_set, 
                        name=instr['name'],
                        text=instr['text']
                        )
                    instruction_obj_new.save()
                return JsonResponse({'status': 'success'})
            except InstructionsSet.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Instruction does not exist'})
        else:  # If instruction_id is not provided, it means we are creating a new instruction
            instruction_set = InstructionsSet.objects.create(name=instruction_set_name)
            instruction_set.save()
            for instr in instructions:
                    instruction_obj_new = Instruction.objects.create(
                        instruction_set=instruction_set, 
                        name=instr['name'],
                        text=instr['text']
                        )
                    instruction_obj_new.save()

            return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


# views.py
@csrf_exempt
def delete_instruction(request):
    if request.method == 'POST':
        instruction_row_id = request.POST.get('instruction_row_id')
        instruction_set_id = request.POST.get('instruction_set_id')
        try:
            instruction_setObj = InstructionsSet.objects.get(id=instruction_set_id)
            all_instructions_row = Instruction.objects.filter(instruction_set=instruction_setObj)
            if len(all_instructions_row)>1:
                desired_instruction_row = Instruction.objects.get(instruction_set= instruction_setObj , id = instruction_row_id)
                desired_instruction_row.delete()
            else:
                instruction_setObj.delete()
            return JsonResponse({'status': 'success'})
        except InstructionsSet.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Instruction does not exist'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required(login_url="myauth:loginPage")
def query_prompt_text(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            voice_type = data.get('voice_type')
            temperature = data.get('temperature')
            presence_penalty = data.get('presence_penalty')
            frequency_penalty = data.get('frequency_penalty')
            model = data.get('model')
            limit = int(data.get('limit')) 
            prompt_text = data.get('prompt_text')
            system_prompt = data.get('system_prompt')
            memory = request.session.get('memory', [""])
            combined_prompt = create_combined_prompt(memory, prompt_text, voice_type, limit)
            api_key = get_api_key(model)
            print(" system_prompt ", system_prompt)

            # Check if the API is active
            if not is_api_active(model):
                return JsonResponse({'success': False, 'error': f'{model} API key is not saved properly or is inactive.'})
        
            if model == "OpenAI":
                try:
                 variants = generate_openai_variants(api_key, combined_prompt, float(temperature), int(presence_penalty), int(frequency_penalty), system_prompt)
                except AuthenticationError:
                    return JsonResponse({'result': False, 'error': 'Authentication failed. Please check your API key'}, status=401)
                except Exception as e:
                    print("e is ", e)
                    return JsonResponse({'result': False, 'error': 'An error occurred: '+str(e)}, status=500)

    
            elif model == "Claude":
                variants = generate_claude_variants(api_key, combined_prompt, float(temperature), system_prompt)
            else:
                return JsonResponse({'result': False, 'error': 'Invalid request method'}, status=405)
            
            with open('output.json', 'w') as f:
                json.dump(variants, f, indent=4)
            # Process the data as needed
            result = True  # or False based on your processing logic
            print("variants are : ", variants)
            return JsonResponse({'result': result, 'variants': variants})
        except json.JSONDecodeError:
            return JsonResponse({'result': False, 'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'result': False, 'error': 'Invalid request method'}, status=405)


@csrf_exempt
def update_memory(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            new_memory = data.get('memory')
            if new_memory is None:
                return JsonResponse({'result': False, 'error': 'Memory not provided'}, status=400)
            
            memory = request.session.get('memory', [])
            if not isinstance(memory, list):
                memory = []

            if len(memory) > 0 and memory[-1].get('instruction') == new_memory.get('instruction'):
                # Replace the answer of the last memory entry
                memory[-1]['answer'] = new_memory['answer']
            else:
                # Append the new memory entry
                memory.append(new_memory)
            request.session['memory'] = memory
            request.session.modified = True     
            memory_json = json.dumps(memory)       
            return JsonResponse({'result': True, 'memory':memory, 'memory_json':memory_json })
        except json.JSONDecodeError:
            return JsonResponse({'result': False, 'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'result': False, 'error': 'Invalid request method'}, status=405)


@csrf_exempt
def clear_memory(request):
    if request.method == 'POST':
        try:
            if 'memory' in request.session:
                del request.session['memory']
                request.session.modified = True
            return JsonResponse({'result': True, 'message': 'Memory cleared'})
        except Exception as e:
            return JsonResponse({'result': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'result': False, 'error': 'Invalid request method'}, status=405)


@login_required(login_url="myauth:loginPage")
@csrf_exempt
def setting_page(request):
    if request.method == 'POST':
        try:
            print("inside is method : ")
            print("data is : ", request.POST)
            Claude_API = request.POST.get('Claude_API')
            OpenAI_API = request.POST.get('OpenAI_API')
            setting_page_obj, created = SettingPage.objects.get_or_create(id=1)
            if Claude_API and OpenAI_API:
                setting_page_obj.Claude_API = Claude_API
                setting_page_obj.OpenAI_API = OpenAI_API
                setting_page_obj.save()
                return JsonResponse({'result': True, 'details': "Keys updated successfully", "Claude_API":Claude_API, "OpenAI_API":OpenAI_API}, status=200)
            else:
                return JsonResponse({'result': False, 'error': "Keys can not be empty"}, status=500)
        except Exception as e:
            return JsonResponse({'result': False, 'error': str(e)}, status=500)
    else:
        setting_page_obj = SettingPage.objects.first()
        if setting_page_obj is None:
            Claude_API = ''
            OpenAI_API = ''
        else:
            Claude_API = setting_page_obj.Claude_API
            OpenAI_API = setting_page_obj.OpenAI_API

        context = {
            'Claude_API': Claude_API,
            'OpenAI_API': OpenAI_API
        }
        return render(request, 'promptapp/setting_page.html', context)


@login_required(login_url="myauth:loginPage")
def instructions_theme(request):
    memory = request.session.get('memory', [])
    if not isinstance(memory, list):
                memory = []
    instructions_theme = InstructionsTheme.objects.all()
    instructions_data = [
        {
            'set_id': instruction_theme.id,
            'set_name': instruction_theme.name,
            'instructions': list(instruction_theme.instructionsThemeRow.values('id', 'name','text'))
        }
        for instruction_theme in instructions_theme
    ]
    instructions_json = json.dumps(instructions_data)
    memory_json = json.dumps(memory)
    print("instructions_theme: ", instructions_json)
    print("memory_json: ", memory_json)
    context = {
        'memory_array': memory_json,
        'instructions_theme': instructions_theme,
        'instructions_data': instructions_json
    }
    return render(request, 'promptapp/instructionstheme.html', context)



# views.py
@csrf_exempt
def save_or_edit_instructiontheme(request):
    if request.method == 'POST':
        # print("request post : ", (request.POST))
        instruction_id = request.POST.get('instruction_id')  # For editing, this will be provided
        if instruction_id:
            instruction_id = int(instruction_id)
        else:
            instruction_id = ""  # or set it to some default value
        # print("instruction_id : ", instruction_id)
        instruction_theme_name = request.POST.get('instruction_theme_name')
        instructions = json.loads(request.POST.get('instructions', '[]'))
        
        # Create new InstructionsSet

        if instruction_id:  # If instruction_id is provided, it means we are editing existing instruction
            try:
                instruction_theme = InstructionsTheme.objects.get(id=instruction_id)
                instruction_theme.name = instruction_theme_name
                instruction_theme.save()

                InstructionsThemeRow.objects.filter(instruction_theme_id=instruction_id).delete()

                for instr in instructions:
                    instruction_obj_new = InstructionsThemeRow.objects.create(
                        instruction_theme=instruction_theme, 
                        name=instr['name'],
                        text=instr['text']
                        )
                    instruction_obj_new.save()
                return JsonResponse({'status': 'success'})
            except InstructionsSet.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Instruction does not exist'})
        else:  # If instruction_id is not provided, it means we are creating a new instruction
            instruction_theme = InstructionsTheme.objects.create(name=instruction_theme_name)
            instruction_theme.save()
            for instr in instructions:
                    instruction_obj_new = InstructionsThemeRow.objects.create(
                        instruction_theme=instruction_theme, 
                        name=instr['name'],
                        text=instr['text']
                        )
                    instruction_obj_new.save()

            return JsonResponse({'status': 'success'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

# views.py
@csrf_exempt
def delete_instruction_theme(request):
    if request.method == 'POST':
        instruction_row_id = request.POST.get('instruction_row_id')
        instruction_theme_id = request.POST.get('instruction_theme_id')
        print("instruction_set_id: ", instruction_theme_id)
        print("instruction_row_id: ", instruction_row_id)
        try:
            instruction_setObj = InstructionsTheme.objects.get(id=instruction_theme_id)
            all_instructions_row = InstructionsThemeRow.objects.filter(instruction_theme=instruction_setObj)
            if len(all_instructions_row)>1:
                desired_instruction_row = InstructionsThemeRow.objects.get(instruction_theme= instruction_setObj , id = instruction_row_id)
                desired_instruction_row.delete()
            else:
                instruction_setObj.delete()
            return JsonResponse({'status': 'success'})  
        except InstructionsSet.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Instruction does not exist'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})



def validate_claude_api_key(api_key):
    client = anthropic.Anthropic(api_key=api_key)
    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": "This is dummy prompt to validate API"}
            ],
            temperature= 1,
            timeout=3000
        )
        return True  # API key is valid if no exception is raised
    except Exception as e:
        return False  # API key is invalid


@csrf_exempt
def save_claude_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        claude_api_key = data.get('claude_api_key')
        print("in save claude, ", claude_api_key)
        if claude_api_key == "" or None:
            setting_page_obj = SettingPage.objects.first()
            setting_page_obj.Claude_API = claude_api_key
            setting_page_obj.Claude_API_status = False
            setting_page_obj.save()
            return JsonResponse({'success': True})
        if validate_claude_api_key(claude_api_key):
            setting_page_obj = SettingPage.objects.first()
            setting_page_obj.Claude_API = claude_api_key
            setting_page_obj.Claude_API_status = True
            setting_page_obj.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False})     


def validate_openai_api_key(api_key):
    try:
        client = OpenAI(api_key=api_key)
        # OpenAI.api_key = api_key
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "This is a system prompt for validation."},
                {"role": "user", "content": "This is a test prompt to validate the API key."}
            ],
            temperature=0.1,
            presence_penalty=0,
            frequency_penalty=0,
            n=1
        )
        return True  # API key is valid if no exception is raised
    except Exception as e:
        return False  # API key is invalid


@csrf_exempt
def save_openai_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        openai_api_key = data.get('openai_api_key')
        validation_response = validate_openai_api_key(openai_api_key)
        print("openai_api_key: ", openai_api_key)
        print("validation_response: ", validation_response)
        if openai_api_key == "" or None:
            setting_page_obj = SettingPage.objects.first()
            setting_page_obj.OpenAI_API = openai_api_key
            setting_page_obj.OpenAI_API = False
            setting_page_obj.save()
            return JsonResponse({'success': True})
        
        if validation_response:
            setting_page_obj = SettingPage.objects.first()
            setting_page_obj.OpenAI_API = openai_api_key
            setting_page_obj.OpenAI_API_status = True
            setting_page_obj.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False})
       

def is_api_active(api_name):
    setting_page_obj = SettingPage.objects.first()
    if api_name == 'Claude':
        return setting_page_obj.Claude_API_status
    elif api_name == 'OpenAI':
        return setting_page_obj.OpenAI_API_status
    return False


@login_required(login_url="myauth:loginPage")
def export_themes(request):
    # Define the HttpResponse with the CSV content type
    response = HttpResponse(content_type='text/csv')
    # Specify the CSV file name
    response['Content-Disposition'] = 'attachment; filename="Themes.csv"'
    # Create a CSV writer
    writer = csv.writer(response)
    # Write the CSV header row
    writer.writerow(['Theme Set Name', 'Theme Name', 'Theme Prompt'])
    # Fetch all themes
    themes = InstructionsSet.objects.all()
    # Iterate over each theme
    for theme in themes:
        # Fetch all instructions associated with the current theme
        instructions = theme.instructions.all()
        # Iterate over each instruction
        for instruction in instructions:
            # Write a row to the CSV file for each instruction
            writer.writerow([theme.name, instruction.name, instruction.text])

    # Return the response to download the CSV file
    return response


@csrf_exempt
@login_required(login_url="myauth:loginPage")
def import_themes(request):
    try:
        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            messages.error(request, "This is not a CSV file.")
            return redirect('your_redirect_url')

        data_set = file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        next(io_string)  # Skip the header row

        for row in csv.reader(io_string, delimiter=',', quotechar='"'):
            theme_name, instruction_name, instruction_text = row
            set, created = InstructionsSet.objects.get_or_create(name=theme_name)
            Instruction.objects.create(
                instruction_set=set,
                name=instruction_name,
                text=instruction_text
            )
        messages.success(request, "Themes imported successfully.")
    except Exception as e:
        messages.error(request, f"Error importing themes: {e}")



# export impot of instructions now


@login_required(login_url="myauth:loginPage")
def export_instructions(request):
    print("in 1")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="Instructions.csv"'

    writer = csv.writer(response)
    writer.writerow(['Insructions Set Name', 'Instruction Name', 'Instruction Prompt'])

    themes = InstructionsTheme.objects.all()

    for theme in themes:
        rows = theme.instructionsThemeRow.all()
        for row in rows:
            writer.writerow([theme.name, row.name, row.text])

    return response


@csrf_exempt
@login_required(login_url="myauth:loginPage")
def import_instructions(request):
    try:
        file = request.FILES['file']
        if not file.name.endswith('.csv'):
            messages.error(request, "This is not a CSV file.")
            return redirect('your_redirect_url')

        data_set = file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        next(io_string)  # Skip the header row

        for row in csv.reader(io_string, delimiter=',', quotechar='"'):
            instructionsSet_name, instruction_name, prompt_text = row
            theme, created = InstructionsTheme.objects.get_or_create(name=instructionsSet_name)
            InstructionsThemeRow.objects.create(
                instruction_theme=theme,
                name=instruction_name,
                text=prompt_text
            )
        messages.success(request, "Instruction Sets imported successfully.")
    except Exception as e:
        messages.error(request, f"Error importing instruction set: {e}")