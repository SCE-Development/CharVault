"use client";
import { useActionState } from "react";
import Link from "next/link";
import { actions } from "@/src/data/actions";

import {
    CardTitle,
    CardDescription,
    CardHeader,
    CardContent,
    CardFooter,
    Card,
} from "@/src/components/ui/card";

import { Label } from "@/src/components/ui/label";
import { Input } from "@/src/components/ui/input";
import { Button } from "@/src/components/ui/button";

const styles = {
    container: "w-full max-w-md",
    header: "space-y-1",
    title: "text-3xl font-bold text-pink-500",
    content: "space-y-4",
    fieldGroup: "space-y-2",
    footer: "flex flex-col",
    button: "w-full",
    prompt: "mt-4 text-center text-sm",
    link: "ml-2 text-pink-500",
};

const INITIAL_STATE = {
    data: {
        username: "",
        password: "",
        email: "",
    },
};

export function SignupForm() {
    const [formState, formAction] = useActionState(
        actions.auth.registerUserAction,
        INITIAL_STATE
    );

    console.log("## will render on client ##");
    console.log(formState);
    console.log("###########################");
    return (
        <div className={styles.container}>
            <form action={formAction}>
                <Card>
                    <CardHeader className={styles.header}>
                        <CardTitle className={styles.title}>Sign Up</CardTitle>
                        <CardDescription>
                            Enter your details to create a new account
                        </CardDescription>
                    </CardHeader>
                    <CardContent className={styles.content}>
                        <div className={styles.fieldGroup}>
                            <Label htmlFor="username">Username</Label>
                            <Input
                                id="username"
                                name="username"
                                type="text"
                                placeholder="username"
                            />
                        </div>
                        <div className={styles.fieldGroup}>
                            <Label htmlFor="email">Email</Label>
                            <Input
                                id="email"
                                name="email"
                                type="email"
                                placeholder="name@example.com"
                            />
                        </div>
                        <div className={styles.fieldGroup}>
                            <Label htmlFor="password">Password</Label>
                            <Input
                                id="password"
                                name="password"
                                type="password"
                                placeholder="password"
                            />
                        </div>
                    </CardContent>
                    <CardFooter className={styles.footer}>
                        <Button className={styles.button}>Sign Up</Button>
                    </CardFooter>
                </Card>
                <div className={styles.prompt}>
                    Have an account?
                    <Link className={styles.link} href="signin">
                        Sign In
                    </Link>
                </div>
            </form>
        </div>
    );
}