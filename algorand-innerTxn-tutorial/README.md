# Tutorial for using Inner Transactions using *PyTEAL*

it contains:

- Example Scenario (**License Manager Contract**)
- additional *PyTEAL* code examples for **Inner Transactions**
- bash script for (automatically) executing functions of the **License Manager Contract** using the *goal SDK*

## How to run your own version:
First you need to have a *PyTEAL* version that supports *TEAL v5* installed.
Therefore you can just go to the *PyTEAL* github repository and get the latest version of *PyTEAL*:
```
git clone https://github.com/algorand/pyteal.git
cd pyteal
pip install -e 
```

Then you can grab the repository:
`git clone https://github.com/JuWeber99/algorand-innerTxn-tutorial`

To then run it in the sandbox:

`#host >$SANDBOX_DIR/sandbox up dev`

Get 2 Account addresses from the output of `goal account list` and paste them into the `app_creator` and `client` variables of the **interactions.sh** bash script under **$REPO_DIR/src/interactions.sh**
Then you can copy the compiled contract and the bash script to your sandbox:
```
#host >$SANDBOX_DIR/sandbox copyTo $REPO_DIR/src/interactions.sh
#host >$SANDBOX_DIR/sandbox copyTo $REPO_DIR/innerTxn_tutorial_pyteal.teal
```

Now you are ready to go!

## Execute interactions

Now you can use the **interactions.sh** bash script to interact with the application!

```
#host >$SANDBOX_DIR/sandbox enter algod
#sandbox >chmod +x interactions.sh 
#sandbox >./interactions.sh

```

## Inner Transaction snippets

To grab some snippets of *PyTEAL* - **Subroutines** to create all kinds of **Inner Transactions** look into the **$REPO_DIR/src/inner_txn_snippets/\*.py** 