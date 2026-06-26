ctWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(results)

if __name__=='__main__':
    main()
