from PIL import Image, ImageDraw
import os
import io
import base64

class highlighter:
    def __init__(self, screenshot_dir="screenshots", outline_color="red", line_width=5, padding=10, scale_factor=1.5):
        
        self.outline_color = outline_color
        self.line_width = line_width
        self.padding = padding
        self.scale_factor = scale_factor
        self.screenshot_dir = screenshot_dir
        os.makedirs(self.screenshot_dir, exist_ok=True)

    def highlight_element(self, driver, element, testcase_name="default_test"):
        """
        Method name: highlight_element
        Author: Nadil Rudhainif (nadil.rudhainif@ibm.com)
        Description: Captures a screenshot with the given element highlighted.
        Parameters:
            driver: Selenium WebDriver instance.
            element: Selenium WebElement to highlight.
            testcase_name (str): Name used in the screenshot filename.
        Returns:
            str: Path to the saved screenshot.
        """
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        device_pixel_ratio = driver.execute_script("return window.devicePixelRatio;")
        location = element.location_once_scrolled_into_view
        size = element.size

        left = int((location['x'] - self.padding) * device_pixel_ratio)
        top = int((location['y'] - self.padding) * device_pixel_ratio)
        right = int((location['x'] + size['width'] + self.padding) * device_pixel_ratio)
        bottom = int((location['y'] + size['height'] + self.padding) * device_pixel_ratio)

        screenshot_base64 = driver.get_screenshot_as_base64()
        image = Image.open(io.BytesIO(base64.b64decode(screenshot_base64)))

        draw = ImageDraw.Draw(image)
        draw.rectangle(
            [left, top, right, bottom],
            outline=self.outline_color,
            width=self.line_width
        )

        if self.scale_factor and self.scale_factor != 1.0:
            new_size = (
                int(image.width * self.scale_factor),
                int(image.height * self.scale_factor)
            )
            image = image.resize(new_size, Image.LANCZOS)

        screenshot_path = os.path.join(self.screenshot_dir, f"{testcase_name}.png")
        image.save(screenshot_path)

        return screenshot_path
