from utils.db_clean import *

if __name__ == "__main__":
    try:
        project = sys.argv[1]
        setdelete = sys.argv[2]
        print(f'project={project} \n ')
        print(f'setdelete: {setdelete}')
        clean = DbCleanup(project, setdelete)

    except Exception as e:
        print(f'Db cleanup failed with error : {e}')
        raise Exception(f"Db cleanup failed with error .")