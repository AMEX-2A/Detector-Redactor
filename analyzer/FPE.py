from Crypto.Cipher import AES
import re
import string

class FPE:
    """
    Format-Preserving Encryption (FPE) operator.
    This operator encrypts text while preserving the original format, including digits and alphabetic characters.
    """

    def __init__(self, key):
        # Store the encryption key but do not initialize the cipher yet
        self.key = key
        self.operator_name = "custom_fpe"

    def operate(self, text: str, params: dict = None):
        """
        Encrypt the text while preserving its original format (digits and letters, etc.).
        """
        # Preserve original format by handling both digits and alphabetic characters
        digits = re.sub(r'\D', '', text)
        letters = re.sub(r'[^a-zA-Z]', '', text)

        # Encrypt digits and letters separately using the same cipher key
        encrypted_digits = self._encrypt_component(digits)
        encrypted_letters = self._encrypt_component(letters)

        # Rebuild the original text format by replacing digits and letters with their encrypted versions
        result = []
        digit_idx, letter_idx = 0, 0

        for char in text:
            if char.isdigit():
                result.append(encrypted_digits[digit_idx])
                digit_idx += 1
            elif char.isalpha():
                result.append(encrypted_letters[letter_idx])
                letter_idx += 1
            else:
                result.append(char)  # Leave non-alphanumeric characters unchanged

        return ''.join(result)

    def _encrypt_component(self, component: str):
        """
        Encrypt a component of the text (either digits or letters) using AES and preserve its length.
        """
        if not component:
            return ""

        # Create a new AES cipher instance for each encryption operation
        cipher = AES.new(self.key, AES.MODE_EAX)

        # Encrypt the component
        ciphertext, tag = cipher.encrypt_and_digest(component.encode())

        # Convert ciphertext into a mapped format (digits or letters based on input)
        if component.isdigit():
            # Map to digits
            encrypted_component = ''.join([str(ord(c) % 10) for c in ciphertext.decode('latin-1')])
        elif component.isalpha():
            # Map to alphabet letters
            alphabet = string.ascii_letters
            encrypted_component = ''.join([alphabet[ord(c) % len(alphabet)] for c in ciphertext.decode('latin-1')])

        return encrypted_component[:len(component)]  # Ensure the length is preserved

    def validate(self, params: dict = None):
        """
        Ensure the required encryption parameters are provided.
        """
        if not params or "key" not in params:
            raise ValueError("Encryption requires a valid key.")
