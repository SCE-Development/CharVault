type RegisterUserState = {
    data: {
        username: string;
        password: string;
        email: string;
    };
};

export async function registerUserAction(
    prevState: RegisterUserState,
    formData: FormData
): Promise<RegisterUserState> {
    console.log("Hello From Register User Action");

    const fields = {
        username: formData.get("username") as string,
        password: formData.get("password") as string,
        email: formData.get("email") as string,
    };

    console.log("#############");
    console.log(fields);
    console.log("#############");

    return {
        ...prevState,
        data: fields,
    };
}