import uuid

import ai_marketplace_hub.universal_schema.data_types as dt
import ai_marketplace_hub.universal_schema.task_schema_functions as df

from superai import SuperAI, Template, Worker, Task

# Using uuid.getnode() to get a unique name for your first template
TEMPLATE_NAME = "MyFirstWorkflow" + str(uuid.getnode())

dp_definition = {
    "input_schema": dt.bundle(mnist_image_url=dt.IMAGE),
    "parameter_schema": dt.bundle(instructions=dt.TEXT, choices=dt.array_to_schema(dt.TEXT, 0)),
    "output_schema": dt.bundle(mnist_class=dt.EXCLUSIVE_CHOICE),
}

dp_template = Template(name=TEMPLATE_NAME, definition=dp_definition, add_basic_workflow=False)


def my_workflow(inputs, params, **kwargs):
    """
    Simple hello world MNIST workflow
    :param inputs:
    :return:
    """
    print(f"{dp_template.name}.my_workflow: Arguments: inputs {inputs} params: {params}, **kwargs: {kwargs} ")

    task1 = Task(name="is_number")
    task1_inputs = [
        df.text("Is this image a number"),
        df.image(inputs.get("mnist_image_url")),
    ]
    task1_outputs = [df.exclusive_choice(choices=["yes", "no"])]
    task1(task_inputs=task1_inputs, task_outputs=task1_outputs)
    task1_response = task1.output.get("values", [])[0].get("schema_instance")

    if task1_response.get("selection", {}).get("value") == "yes":
        task2 = Task(name="choose_number")
        task2_inputs = [
            df.text("Choose the correct number"),
            df.image(inputs.get("mnist_image_url")),
        ]
        task2_outputs = [df.exclusive_choice(choices=params.get("choices", []))]
        task2(task_inputs=task2_inputs, task_outputs=task2_outputs)
    else:
        return {"mnist_class": {"choices": df.build_choices(params.get("choices", []))}}

    return {"mnist_class": task2.output.get("values", [])[0].get("schema_instance")}


dp_template.add_workflow(my_workflow, name="my_mnist_workflow_1", default=True)

superAI = SuperAI(
    template=dp_template,
    name="FirstSuperAIWorfklow",
    params={
        "instructions": "Select the appropriate class for the MNIST image",
        "choices": ["0", "1", "2", "3"],
    },
    performance={"quality": {"f1": 0.9}},
)

mnist_urls = [
    "https://superai-public.s3.amazonaws.com/example_imgs/digits/0zero.png",
    "https://superai-public.s3.amazonaws.com/example_imgs/digits/1one.png",
]
inputs = [{"mnist_image_url": url} for url in mnist_urls]

labels = superAI.process(inputs=inputs, worker=Worker.me, open_browser=True)